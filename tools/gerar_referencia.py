"""Gera docs/REFERENCIA_MODULOS.md a partir do código do projeto.

Nomes, assinaturas, números de linha e docstrings vêm dos arquivos; o papel
de cada módulo e o significado das constantes são os textos deste script.
Se uma função ou constante nova não tiver descrição, o script para e diz
qual é.

Uso:
    python tools/gerar_referencia.py
"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

ORDER = ["main.py", "src/pipeline.py", "src/config.py", "src/storage.py",
         "src/github_collector.py", "src/text_preprocessor.py", "src/regex_analyzer.py",
         "src/nlp_analyzer.py", "src/technology_analyzer.py", "src/debt_classifier.py",
         "src/sentiment_analyzer.py", "src/statistics_analyzer.py", "src/report.py"]

ROLE = {
    "main.py": (
        "Ponto de entrada. Lê as opções da linha de comando, faz as perguntas do modo "
        "interativo, chama o pipeline e transforma os erros em mensagens. Não contém "
        "nenhuma regra de análise.",
        "Três caminhos: `--check` chama `run_check`; `--text` chama `run_explanation`; "
        "o restante chama `run_pipeline`, que coleta (ou lê um arquivo com `--file`), "
        "analisa, grava e mostra o relatório."),
    "src/pipeline.py": (
        "Orquestra as etapas. Cada etapa é uma função curta que chama o módulo "
        "responsável, grava o resultado em uma chave do documento e mostra uma linha "
        "de andamento.",
        "`collect` e `load` são as duas formas de obter a coleta (passo 1). `analyze` "
        "executa os passos 2 a 7. `explain` reaproveita os mesmos módulos para um "
        "único texto, sem gravar nada."),
    "src/config.py": (
        "Reúne os caminhos do projeto e a leitura validada do arquivo `.env`. É o "
        "único lugar que lê variáveis de ambiente; os outros módulos recebem um "
        "objeto `Config` pronto.",
        "Variáveis aceitas no `.env`: `GITHUB_TOKEN`, `SPACY_MODEL` e "
        "`DEFAULT_ISSUES`. Variáveis já definidas no terminal têm prioridade."),
    "src/storage.py": (
        "Leitura e gravação de JSON em UTF-8. Existe para que o formato de gravação "
        "(indentação, acentos sem escape) seja o mesmo em todo o projeto.", ""),
    "src/github_collector.py": (
        "Fala com a API REST do GitHub. Busca issues, pull requests e commits, junta "
        "os comentários e devolve tudo em um formato único de registro.",
        "A paginação segue o cabeçalho `Link`. Os erros de rede e de HTTP viram "
        "`GitHubError` com mensagem em português. Se o limite da API acaba durante "
        "os comentários, a coleta é mantida e o motivo vai para `metadata.warning`."),
    "src/text_preprocessor.py": (
        "Limpa o Markdown e transforma um registro coletado em um documento pronto "
        "para análise. Separa os blocos de código em um campo próprio e descarta o "
        "que foi escrito por bots.",
        "`clean_text` aplica as expressões em cinco passos numerados no código: "
        "normalização de caracteres, separação do código, remoção do que não é "
        "texto, retirada da formatação e normalização dos espaços. A ordem importa: "
        "os blocos de código saem antes de qualquer outra regra tocar no texto."),
    "src/regex_analyzer.py": (
        "Procura os padrões de dívida técnica com expressões regulares. Cada padrão "
        "tem nome, categoria e nível (explícito ou de contexto).",
        "Um trecho do texto é contado uma vez só: a lista `PATTERNS` é percorrida em "
        "ordem, e um trecho já contado por um padrão não conta para os seguintes. "
        "Por isso as expressões específicas vêm antes das genéricas, e `debt` é o "
        "último padrão."),
    "src/nlp_analyzer.py": (
        "Análise linguística com spaCy: tokens, lemas, stopwords, classes "
        "gramaticais, expressões nominais e entidades nomeadas.",
        "Acrescenta ao pipeline do spaCy um componente próprio, "
        "`blank_line_sentences`, antes do `parser`. As tecnologias não são tratadas "
        "aqui."),
    "src/technology_analyzer.py": (
        "Identifica tecnologias com uma lista do próprio projeto e o `PhraseMatcher` "
        "do spaCy. Não usa o NER.",
        "Há dois buscadores: um ignora maiúsculas e minúsculas e outro exige a "
        "grafia exata, para nomes que também são palavras comuns. Tokens com barra "
        "são analisados de novo com as partes separadas."),
    "src/debt_classifier.py": (
        "Classifica cada documento em cinco tipos de dívida técnica, com regras. Não "
        "há aprendizado de máquina.",
        "Junta a evidência forte (padrões explícitos da Regex) com a fraca (lemas do "
        "vocabulário de cada tema) e aplica a regra de `decide`. Precisa das chaves "
        "`regex` e `nlp` do documento."),
    "src/sentiment_analyzer.py": (
        "Mede o sentimento com o VADER, por sentença, depois de retirar do léxico a "
        "valência de termos técnicos.",
        "O texto é dividido em sentenças por uma Regex própria, e não pelo spaCy, "
        "para o módulo não depender do modelo."),
    "src/statistics_analyzer.py": (
        "Soma os resultados de todos os documentos e monta o resumo consolidado: "
        "totais, contagens por fonte, classificação, resolução, sentimento, "
        "frequências e linha do tempo.",
        "`has_debt` é a definição de \"dívida identificada\" usada em todo o "
        "projeto. `rank` é a função genérica por trás de todas as listas de "
        "frequência."),
    "src/report.py": (
        "Mostra o resumo consolidado no terminal, em blocos, e a explicação de um "
        "texto na opção `--text`. Lê apenas o resumo; não calcula nada.",
        "A largura é controlada por `WIDTH`, e as listas quebram de linha por item, "
        "para caber em 80 colunas."),
}

CONSTANTS = {
    "BASE_DIR": "Pasta do projeto.",
    "ENV_FILE": "Caminho do arquivo `.env`.",
    "DATA_DIR": "Pasta `data/`.",
    "RAW_DIR": "Coletas, como vieram da API.",
    "PROCESSED_DIR": "Documentos com todas as análises.",
    "RESULTS_DIR": "Resumos consolidados.",
    "GITHUB_API_URL": "Endereço da API. O coletor só segue páginas que comecem por ele.",
    "REQUEST_TIMEOUT": "Segundos de espera por resposta da API.",
    "DEFAULT_SPACY_MODEL": "Modelo usado quando `SPACY_MODEL` não está no `.env`.",
    "DEFAULT_ISSUES": "Quantidade sugerida quando o programa pergunta.",
    "PER_PAGE": "Itens por página pedidos à API (o máximo aceito).",
    "MAX_COMMENTS_PER_ISSUE": "Limite de comentários guardados por issue ou pull request.",
    "SOURCES": "Fontes aceitas por `--source`, na ordem em que aparecem no resultado.",
    "EMAIL": "Regex de endereço de e-mail; não casa com `git@github.com:org/repo` nem `react@18.2.0`.",
    "MASKED_EMAIL": "Endereço fictício que substitui os e-mails coletados.",
    "CODE_BLOCK": "Bloco de código cercado por três ou mais crases ou tis.",
    "HTML_COMMENT": "Comentário HTML.",
    "IMAGE": "Imagem em Markdown; é removida inteira.",
    "LINK": "Link em Markdown; fica só o texto.",
    "URL": "Endereço solto.",
    "HTML_TAG": "Tags HTML conhecidas; placeholders como `<name>` sobrevivem.",
    "GIT_TRAILER": "Assinaturas do Git, como `Co-authored-by:`.",
    "MENTION": "Menção a usuário (`@fulano`).",
    "INLINE_CODE": "Código entre crases; fica o conteúdo.",
    "QUOTE": "Marca de citação no início da linha.",
    "ALERT": "Marcas `[!NOTE]`, `[!WARNING]` e semelhantes.",
    "HEADING": "Cerquilhas de título.",
    "BULLET": "Marcador de item de lista.",
    "CHECKBOX": "Caixa de seleção de lista de tarefas.",
    "TABLE_RULE": "Régua horizontal ou linha divisória de tabela.",
    "TABLE_ROW": "Linha de tabela; as barras viram espaços.",
    "BOLD": "Negrito.",
    "ITALIC": "Itálico com asterisco. Sublinhados são preservados, por causa de `snake_case`.",
    "STRIKE": "Texto riscado.",
    "SPACES": "Sequência de espaços e tabulações.",
    "SPACES_AROUND_NEWLINE": "Espaços colados a uma quebra de linha.",
    "BLANK_LINES": "Três ou mais quebras de linha seguidas.",
    "CURLY_QUOTES": "Tabela que troca aspas curvas por retas.",
    "KNOWN_BOTS": "Contas automáticas que não usam o sufixo `[bot]`. Expansível.",
    "CATEGORIES": None,  # tratado por módulo
    "BEFORE_MARKER": "Trecho de Regex: o marcador não vem depois de letra, `/` ou `.`.",
    "AFTER_MARKER": "Trecho de Regex: o marcador não é seguido de letra, `/` ou extensão.",
    "PATTERNS": "Os 36 padrões, na ordem em que são aplicados.",
    "COMPILED": "Os padrões compilados com `re.IGNORECASE`.",
    "CODE_MARKERS": "Padrões procurados dentro dos blocos de código.",
    "CONTEXT_WIDTH": "Caracteres de contexto guardados antes e depois de cada ocorrência.",
    "RELEVANT_POS": "Classes gramaticais que entram nas frequências.",
    "EXTRA_STOPWORDS": "Palavras ignoradas além das stopwords do spaCy. Expansível.",
    "NUMERIC_LABELS": "Rótulos numéricos do NER, descartados.",
    "MIN_TERM_LENGTH": "Tamanho mínimo de um termo para entrar nas frequências.",
    "TECHNOLOGIES": "As 40 tecnologias, por categoria, cada uma com os seus apelidos. Expansível.",
    "CASE_SENSITIVE": "Nomes que também são palavras comuns e exigem a grafia exata.",
    "ALIASES_ONLY": "Nomes ambíguos demais; só os apelidos são procurados.",
    "YES_THRESHOLD": "Ocorrências de evidência fraca que bastam para confirmar um tipo.",
    "STRONG_PATTERNS": "Padrões explícitos da Regex que confirmam cada tipo.",
    "WEAK_PATTERNS": "Padrões que só sugerem um tipo.",
    "TERMS": "Vocabulário de cada tipo, em forma de lema. Expansível.",
    "TECHNICAL_NEUTRAL": "Os 37 termos técnicos sem valência. Expansível.",
    "NEUTRAL_FUNCTION_WORDS": "Palavras funcionais sem valência própria.",
    "POSITIVE_THRESHOLD": "A partir deste `compound` o rótulo é positivo.",
    "NEGATIVE_THRESHOLD": "Até este `compound` o rótulo é negativo.",
    "SENTENCE_END": "Regex que divide o texto em sentenças.",
    "TOP_TERMS": "Tamanho das listas de termos, expressões e entidades.",
    "TYPE_NAMES": "Tipos de registro, com o nome no singular e no plural.",
    "SENTIMENT_LABELS": "Rótulos de sentimento, na ordem de exibição.",
    "STATUSES": "Resultados possíveis da classificação.",
    "TOTAL_STEPS": "Número de passos mostrados no andamento.",
    "ISSUE_FIELDS": "Campos que todo registro de uma coleta precisa ter.",
    "METADATA_FIELDS": "Campos obrigatórios no `metadata` de uma coleta.",
    "WIDTH": "Largura do relatório, em colunas.",
    "BAR_WIDTH": "Tamanho máximo das barras.",
    "MAX_TIMELINE_ROWS": "Acima disso a linha do tempo é mostrada por ano.",
    "CATEGORY_NAMES": "Nome em português de cada tipo de dívida.",
    "MARKERS": "Marcadores sempre exibidos no bloco de Regex.",
    "EXPRESSIONS": "Expressões sempre exibidas no bloco de Regex.",
}
CATEGORIES_BY_MODULE = {
    "src/regex_analyzer.py": "As seis categorias dos padrões; inclui `general`.",
    "src/debt_classifier.py": "Os cinco tipos de dívida classificados.",
}

# Descrições para o que não tem docstring no código.
MANUAL = {
    ("main.py", "build_parser"): "Define as opções da linha de comando.",
    ("main.py", "main"): "Carrega a configuração, cria as pastas e escolhe o caminho a seguir. Devolve o código de saída.",
    ("src/config.py", "Config.has_github_token"): "Propriedade: verdadeiro se há token configurado.",
    ("src/storage.py", "load_json"): "Lê um arquivo JSON em UTF-8.",
    ("src/storage.py", "save_json"): "Grava um arquivo JSON em UTF-8, indentado e sem escapar acentos.",
    ("src/github_collector.py", "GitHubCollector.__init__"): "Cria a sessão HTTP com os cabeçalhos da API; o token entra só se existir.",
    ("src/github_collector.py", "GitHubCollector._fetch_commits"): "Busca os commits, descartando os de merge.",
    ("src/github_collector.py", "GitHubCollector._fetch_comments"): "Busca os comentários de um registro, até o limite.",
    ("src/github_collector.py", "GitHubCollector._get"): "Faz uma requisição e converte timeout e falha de conexão em `GitHubError`.",
    ("src/github_collector.py", "GitHubCollector._update_rate_limit"): "Guarda a cota restante e o horário de renovação, lidos dos cabeçalhos.",
    ("src/github_collector.py", "GitHubCollector._rate_limit_message"): "Monta a mensagem de limite atingido, com o horário de renovação.",
    ("src/github_collector.py", "GitHubCollector._repo_url"): "Monta o endereço do repositório na API.",
    ("src/pipeline.py", "end_step"): "Mostra o resultado de uma etapa.",
    ("src/regex_analyzer.py", "DebtPattern"): "Um padrão: `name`, `category`, `explicit` e `regex`.",
    ("src/report.py", "section"): "Imprime o título de um bloco, com a linha até a largura do relatório.",
    ("src/report.py", "percent"): "Formata uma parte do total como porcentagem.",
    ("src/report.py", "print_collection"): "Bloco COLETA: repositório, registros coletados e analisados, fontes e período.",
    ("src/report.py", "print_debt"): "Bloco DÍVIDA TÉCNICA: total identificado, por critério, por fonte e por tipo.",
    ("src/report.py", "print_regex"): "Bloco REGEX: marcadores e expressões fixos, mais os outros padrões mais frequentes.",
    ("src/report.py", "print_spacy"): "Bloco SPACY: tokens, lemas, expressões e entidades do NER.",
    ("src/report.py", "print_technologies"): "Bloco TECNOLOGIAS: as oito mais citadas, com barras.",
    ("src/report.py", "print_sentiment"): "Bloco SENTIMENTO: distribuição dos rótulos e média.",
    ("src/report.py", "print_resolution"): "Bloco RESOLUÇÃO: fechamento com e sem dívida. Não aparece se só há commits.",
    ("src/report.py", "print_timeline"): "Bloco TEMPO: registros por mês, ou por ano em períodos longos.",
    ("src/sentiment_analyzer.py", "split_sentences"): "Divide o texto em sentenças.",
    ("src/sentiment_analyzer.py", "label_for"): "Converte um `compound` em rótulo.",
    ("src/sentiment_analyzer.py", "SentimentAnalyzer.__init__"): "Carrega o VADER e retira do léxico os termos neutros.",
    ("src/statistics_analyzer.py", "technology_frequencies"): "Tecnologias mais citadas, com a categoria.",
    ("src/statistics_analyzer.py", "pattern_frequencies"): "Padrões de Regex mais frequentes, com a categoria.",
    ("src/statistics_analyzer.py", "has_category"): "Verdadeiro se o documento tem o tipo de dívida como `yes`.",
    ("src/technology_analyzer.py", "TechnologyAnalyzer.__init__"): "Monta os dois buscadores a partir de `TECHNOLOGIES`.",
}

TESTS = {
    "main.py": "Não há teste automatizado da interface; as opções foram exercitadas manualmente.",
    "src/pipeline.py": "`tests/test_pipeline.py`",
    "src/config.py": "`tests/test_pipeline.py` (validação e proteção do token)",
    "src/storage.py": "Indiretamente, em `tests/test_pipeline.py` e `tests/test_github_collector.py`",
    "src/github_collector.py": "`tests/test_github_collector.py`",
    "src/text_preprocessor.py": "`tests/test_text_preprocessor.py`",
    "src/regex_analyzer.py": "`tests/test_regex_analyzer.py`",
    "src/nlp_analyzer.py": "`tests/test_nlp_and_classification.py`",
    "src/technology_analyzer.py": "`tests/test_nlp_and_classification.py`",
    "src/debt_classifier.py": "`tests/test_nlp_and_classification.py`",
    "src/sentiment_analyzer.py": "`tests/test_nlp_and_classification.py`",
    "src/statistics_analyzer.py": "`tests/test_pipeline.py`",
    "src/report.py": "`tests/test_pipeline.py`",
}


def first_line(node):
    doc = ast.get_docstring(node) or ""
    return doc.split("\n\n")[0].replace("\n", " ").strip()


def signature(node):
    args = [a.arg for a in node.args.args if a.arg != "self"]
    defaults = node.args.defaults
    offset = len(args) - len(defaults)
    parts = []
    for index, name in enumerate(args):
        if index >= offset:
            parts.append(f"{name}={ast.unparse(defaults[index - offset])}")
        else:
            parts.append(name)
    return f"{node.name}({', '.join(parts)})"


def describe(path, name, node):
    return first_line(node) or MANUAL.get((path, name)) or "MISSING"


def cell(text):
    return text.replace("|", "\\|")


def module_section(path):
    source = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    role, detail = ROLE[path]
    lines = [f"## `{path}`", "", f"{len(source.splitlines())} linhas. {role}", ""]
    if detail:
        lines += [detail, ""]

    internal = sorted({(n.module.split(".")[1]) for n in ast.walk(tree)
                       if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("src.")}
                      | {a.name for n in ast.walk(tree)
                         if isinstance(n, ast.ImportFrom) and n.module == "src" for a in n.names})
    lines += [f"- **Importa do projeto:** {', '.join(f'`{name}`' for name in internal) or 'nada'}",
              f"- **Testes:** {TESTS[path]}", ""]

    constants = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    meaning = CONSTANTS.get(target.id)
                    if target.id == "CATEGORIES":
                        meaning = CATEGORIES_BY_MODULE[path]
                    constants.append((target.id, node.lineno, meaning or "MISSING"))
    if constants:
        lines += ["### Constantes", "", "| Nome | Linha | Significado |", "|---|---|---|"]
        lines += [f"| `{name}` | {lineno} | {cell(meaning)} |" for name, lineno, meaning in constants]
        lines.append("")

    rows = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            rows.append((signature(node), node.lineno, describe(path, node.name, node)))
        elif isinstance(node, ast.ClassDef):
            rows.append((f"class {node.name}", node.lineno, describe(path, node.name, node)))
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    rows.append((f"{node.name}.{signature(sub)}", sub.lineno,
                                 describe(path, f"{node.name}.{sub.name}", sub)))
    if rows:
        lines += ["### Funções e classes", "", "| Nome | Linha | O que faz |", "|---|---|---|"]
        lines += [f"| `{cell(name)}` | {lineno} | {cell(text)} |" for name, lineno, text in rows]
        lines.append("")
    return lines


HEADER = """# Referência dos Módulos

Um capítulo por arquivo de código, na ordem em que os dados passam por
eles. Para cada módulo: o papel, do que ele depende, onde está testado,
as constantes que podem ser ajustadas e todas as funções e classes.

Os nomes, as assinaturas e os números de linha foram extraídos do código;
as descrições das funções são as primeiras linhas das docstrings. Funções
cujo nome começa com `_` são internas ao módulo.

Para a visão de conjunto, veja [ARQUITETURA.md](ARQUITETURA.md). Para os
campos dos dados que essas funções trocam, veja
[FORMATO_DOS_DADOS.md](FORMATO_DOS_DADOS.md).

## Índice

| Módulo | Linhas | Papel em uma frase |
|---|---|---|
"""

SHORT = {
    "main.py": "Interface de linha de comando",
    "src/pipeline.py": "Executa as etapas em ordem",
    "src/config.py": "Caminhos e leitura do `.env`",
    "src/storage.py": "JSON em disco",
    "src/github_collector.py": "Coleta pela API do GitHub",
    "src/text_preprocessor.py": "Limpeza do Markdown",
    "src/regex_analyzer.py": "Padrões de dívida com Regex",
    "src/nlp_analyzer.py": "Análise linguística com spaCy",
    "src/technology_analyzer.py": "Tecnologias, por lista própria",
    "src/debt_classifier.py": "Tipo de dívida, por regras",
    "src/sentiment_analyzer.py": "Sentimento com VADER",
    "src/statistics_analyzer.py": "Resumo consolidado",
    "src/report.py": "Relatório no terminal",
}

out = [HEADER.rstrip("\n")]
for path in ORDER:
    count = len((ROOT / path).read_text(encoding="utf-8").splitlines())
    out.append(f"| [`{path}`](#{path.replace('/', '').replace('.', '').replace('_', '_')}) | {count} | {SHORT[path]} |")
out.append("")
for path in ORDER:
    out += module_section(path)

text = "\n".join(out).rstrip() + "\n"
if "MISSING" in text:
    missing = [line for line in text.splitlines() if "MISSING" in line]
    sys.exit("faltam descrições:\n" + "\n".join(missing))
(ROOT / "docs" / "REFERENCIA_MODULOS.md").write_text(text, encoding="utf-8")
print("REFERENCIA_MODULOS.md:", len(text.splitlines()), "linhas")
