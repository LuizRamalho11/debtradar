"""Pipeline completo da 1ª etapa do DebtRadar.

    GitHub API -> coleta -> pré-processamento -> Regex -> spaCy e
    tecnologias -> classificação -> sentimento -> estatísticas -> resultado

Cada etapa acrescenta uma chave ao documento ("regex", "nlp",
"technologies", "classification", "sentiment"). Ao final são gravados
três arquivos:

    data/raw/        a coleta, como veio da API;
    data/processed/  os documentos com todas as análises;
    data/results/    o resumo consolidado do corpus.
"""
from src import config
from src.debt_classifier import classify_document
from src.github_collector import GitHubCollector, GitHubError, save_collection
from src.regex_analyzer import analyze_document
from src.report import count
from src.sentiment_analyzer import SentimentAnalyzer
from src.statistics_analyzer import TYPE_NAMES, build_summary, has_debt
from src.storage import load_json, save_json
from src.text_preprocessor import clean_text, is_bot, preprocess_issue

TOTAL_STEPS = 7

# Campos que todo registro de uma coleta precisa ter para ser analisado.
ISSUE_FIELDS = {"number", "title", "body", "author", "state", "labels", "created_at",
                "updated_at", "closed_at", "url", "comments_count", "comments"}
METADATA_FIELDS = {"owner", "repo", "label", "collected", "warning"}


class PipelineError(Exception):
    """Erro que interrompe o pipeline, com mensagem pronta para o usuário."""


def start_step(number, message):
    """Mostra o início de uma etapa; o resultado sai na mesma linha."""
    print(f"[{number}/{TOTAL_STEPS}] {message:<27}", end="", flush=True)


def end_step(detail):
    print(detail)


def describe_records(records):
    """Resume uma coleta por tipo: "30 issues, 20 pull requests, 14 comentários"."""
    parts = []
    for name, names in TYPE_NAMES.items():
        # Coletas antigas só tinham issues e não gravavam o tipo.
        total = sum(1 for record in records if record.get("type", "issue") == name)
        if total:
            parts.append(count(total, names))
    comments = sum(len(record["comments"]) for record in records)
    if comments:
        parts.append(count(comments, ("comentário", "comentários")))
    return ", ".join(parts)


def show_records(records):
    """Fecha a etapa 1; o detalhe por tipo vai para outra linha se for longo."""
    detail = describe_records(records)
    if len(detail) <= 45:
        end_step(detail)
    else:
        end_step(count(len(records), ("registro", "registros")))
        print(f"      {detail}")


def load_spacy(model_name):
    """Carrega o pipeline do spaCy e o buscador de tecnologias."""
    # Importado aqui para que "python main.py --check" funcione mesmo sem o spaCy.
    from src.nlp_analyzer import load_pipeline
    from src.technology_analyzer import TechnologyAnalyzer
    try:
        nlp = load_pipeline(model_name)
    except OSError:
        raise PipelineError(
            f"modelo '{model_name}' não encontrado. "
            f"Rode: python -m spacy download {model_name}") from None
    return nlp, TechnologyAnalyzer(nlp)


# --- Etapa 1: obter a coleta ---------------------------------------------

def empty_collection_message(owner, repo, label):
    """Explica uma coleta vazia: diz o que foi procurado e o que tentar."""
    where = f"{owner}/{repo}"
    if not label:
        return (f"Nenhum registro encontrado em {where}.\n"
                "      O repositório pode não ter registros da fonte escolhida.")
    # A API devolve uma lista vazia, sem erro, para uma label que não existe:
    # "debt" existe no microsoft/vscode, mas não no psf/requests.
    return (f"Nenhum registro encontrado em {where} com a label \"{label}\".\n"
            "      Essa label pode não existir nesse repositório. Confira em\n"
            f"      https://github.com/{where}/labels ou deixe a label em branco.")


def collect(owner, repo, limit, label, sources, settings):
    """Coleta os registros pela API. Devolve (coleta, arquivo salvo)."""
    start_step(1, "Coletando dados...")
    collector = GitHubCollector(settings.github_token)
    try:
        collection = collector.collect(owner, repo, limit, label, sources)
    except GitHubError as error:
        raise PipelineError(str(error)) from None
    records = collection["issues"]
    if not records:
        raise PipelineError(empty_collection_message(owner, repo, label))

    path = save_collection(collection)
    show_records(records)
    print(f"      Cota da API: restam {collector.rate_limit_remaining} requisições nesta hora.")
    if collection["metadata"]["warning"]:
        print(f"      Aviso: {collection['metadata']['warning']}")
    return collection, path


def load(path):
    """Lê uma coleta já salva, sem usar a rede. Devolve (coleta, arquivo)."""
    start_step(1, "Carregando coleta salva...")
    try:
        collection = load_json(path)
        records = collection["issues"]
        valid = (METADATA_FIELDS <= set(collection["metadata"])
                 and all(ISSUE_FIELDS <= set(record) for record in records))
    except FileNotFoundError:
        raise PipelineError(f"Arquivo não encontrado: {path}") from None
    except OSError as error:  # pasta no lugar de arquivo, sem permissão de leitura
        raise PipelineError(f"Não foi possível ler {path}: {error.strerror}") from None
    except (ValueError, KeyError, TypeError, AttributeError):
        # ValueError cobre JSON inválido e arquivos que não são texto.
        valid = False
    if not valid:
        raise PipelineError(f"O arquivo não é uma coleta do DebtRadar: {path}")
    if not records:
        raise PipelineError("A coleta não tem nenhum registro.")
    show_records(records)
    print(f"      Arquivo: {path.name}")
    return collection, path


# --- Etapas 2 a 7: analisar ----------------------------------------------

def preprocess(collection):
    """Etapa 2: limpa os textos. Devolve (documentos, registros de bots ignorados)."""
    start_step(2, "Pré-processando...")
    # Registros criados por bots (relatórios automáticos de erro, commits do
    # dependabot) ficam de fora: o interesse é o que as pessoas escrevem.
    records = [record for record in collection["issues"] if not is_bot(record["author"])]
    bot_records = len(collection["issues"]) - len(records)
    if not records:
        raise PipelineError("todos os registros coletados foram criados por bots.")
    documents = [preprocess_issue(record) for record in records]
    bot_comments = sum(document["bot_comments_ignored"] for document in documents)
    end_step(count(len(documents), ("documento", "documentos")))
    if bot_records or bot_comments:
        print(f"      Ignorados por serem de bots: "
              f"{count(bot_records, ('registro', 'registros'))} e "
              f"{count(bot_comments, ('comentário', 'comentários'))}.")
    return documents, bot_records


def apply_regex(documents):
    """Etapa 3: procura os padrões de dívida técnica."""
    start_step(3, "Executando Regex...")
    for document in documents:
        document["regex"] = analyze_document(document["text"], document["code"])
    matches = sum(len(document["regex"]["matches"]) for document in documents)
    end_step(f"{count(matches, ('ocorrência', 'ocorrências'))} de padrões")


def apply_spacy(documents, model_name):
    """Etapa 4: análise linguística e tecnologias. Devolve o nome do modelo."""
    start_step(4, "Executando spaCy...")
    from src.nlp_analyzer import analyze_doc
    nlp, technologies = load_spacy(model_name)
    texts = (document["text"] for document in documents)
    for document, doc in zip(documents, nlp.pipe(texts)):
        document["nlp"] = analyze_doc(doc)
        document["technologies"] = technologies.find(doc)
    tokens = sum(document["nlp"]["tokens"] for document in documents)
    names = {tech["name"] for document in documents for tech in document["technologies"]}
    end_step(f"{tokens} tokens, "
             f"{count(len(names), ('tecnologia distinta', 'tecnologias distintas'))}")
    return f"{nlp.meta['lang']}_{nlp.meta['name']} {nlp.meta['version']}"


def classify(documents):
    """Etapa 5: tipo de dívida de cada documento."""
    start_step(5, "Classificando dívida...")
    for document in documents:
        document["classification"] = classify_document(document)
    with_debt = sum(1 for document in documents if has_debt(document))
    end_step(f"{count(with_debt, ('documento', 'documentos'))} com dívida")


def measure_sentiment(documents):
    """Etapa 6: sentimento de cada documento."""
    start_step(6, "Analisando sentimento...")
    analyzer = SentimentAnalyzer()
    for document in documents:
        document["sentiment"] = analyzer.analyze(document["text"])
    sentences = sum(document["sentiment"]["sentences"] for document in documents)
    end_step(count(sentences, ("sentença pontuada", "sentenças pontuadas")))


def analyze(collection, settings):
    """Executa as etapas 2 a 7. Devolve (documentos analisados, resumo)."""
    documents, bot_records = preprocess(collection)
    apply_regex(documents)
    model = apply_spacy(documents, settings.spacy_model)
    classify(documents)
    measure_sentiment(documents)

    start_step(7, "Gerando resultados...")
    metadata = dict(collection["metadata"])
    metadata["bot_issues_ignored"] = bot_records
    metadata["spacy_model"] = model
    summary = build_summary(documents, metadata)
    end_step("resumo consolidado")
    return documents, summary


def save_results(documents, summary, raw_path):
    """Grava os documentos analisados e o resumo. Devolve os dois caminhos."""
    processed_path = config.PROCESSED_DIR / raw_path.name
    summary_path = config.RESULTS_DIR / f"{raw_path.stem}_summary.json"
    save_json({"metadata": summary["metadata"], "documents": documents}, processed_path)
    save_json(summary, summary_path)
    return processed_path, summary_path


# --- Um texto só, para demonstração --------------------------------------

def explain(text, settings):
    """Passa um único texto por todas as análises e devolve cada resultado."""
    from src.nlp_analyzer import analyze_doc, describe_tokens
    clean, code = clean_text(text)
    nlp, technologies = load_spacy(settings.spacy_model)
    doc = nlp(clean)
    regex = analyze_document(clean, code)
    return {
        "text": clean,
        "code": code,
        "regex": regex,
        "tokens": describe_tokens(doc),
        "technologies": technologies.find(doc),
        "classification": classify_document({"regex": regex, "nlp": analyze_doc(doc)}),
        "sentiment": SentimentAnalyzer().analyze(clean),
    }
