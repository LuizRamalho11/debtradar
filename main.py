"""DebtRadar — Analisador Multimodal de Dívida Técnica (1ª etapa: texto).

Ponto de entrada do programa. Coleta issues, pull requests ou commits de um
repositório do GitHub e executa o pipeline completo: pré-processamento,
Regex, spaCy, tecnologias, classificação, sentimento e estatísticas.

Uso:
    python main.py                      pergunta owner, repositório e quantidade
    python main.py --owner microsoft --repo vscode --limit 30 --label debt
    python main.py --owner psf --repo requests --limit 20 --source all
                                        issues, pull requests e commits
    python main.py --file data/raw/microsoft_vscode_debt_issues.json
                                        analisa uma coleta salva, sem usar a API
    python main.py --text "This needs refactoring and has no tests."
                                        mostra a análise de um texto, passo a passo
    python main.py --check              só verifica a configuração e o ambiente
"""
import argparse
import platform
import sys
from pathlib import Path

from src import config, pipeline
from src.github_collector import SOURCES
from src.report import print_explanation, print_report


def check_spacy_model(model_name):
    """Tenta carregar o modelo do spaCy. Devolve (ok, mensagem)."""
    try:
        import spacy
    except ImportError:
        return False, "spaCy não instalado. Rode: pip install -r requirements.txt"
    try:
        nlp = spacy.load(model_name)
    except OSError:
        return False, (
            f"modelo '{model_name}' não encontrado. "
            f"Rode: python -m spacy download {model_name}"
        )
    return True, f"{model_name} {nlp.meta['version']} (spaCy {spacy.__version__})"


def run_check(settings):
    """Mostra a configuração carregada e verifica se o ambiente está pronto."""
    if settings.has_github_token:
        token_status = "configurado"
    else:
        token_status = "não configurado (limite de 60 requisições/hora)"
    spacy_ok, spacy_message = check_spacy_model(settings.spacy_model)

    print("Configuração")
    print(f"  Token do GitHub : {token_status}")
    print(f"  Modelo spaCy    : {settings.spacy_model}")
    print(f"  Qtd. sugerida   : {settings.default_issues} issues")
    print(f"  Pasta de dados  : {config.DATA_DIR}")
    print()
    print("Ambiente")
    print(f"  Python          : {platform.python_version()}")
    print(f"  spaCy           : {spacy_message}")
    print()
    if not spacy_ok:
        print("Ambiente incompleto: resolva o item acima antes de continuar.")
        return 1
    print("Ambiente pronto.")
    return 0


def ask(prompt):
    """Lê uma resposta do usuário; sem terminal interativo, explica o que fazer."""
    try:
        return input(prompt).strip()
    except EOFError:
        raise pipeline.PipelineError(
            "não há terminal para responder às perguntas. "
            "Use as opções --owner, --repo e --limit.") from None


def ask_parameters(args, settings):
    """Completa, perguntando ao usuário, o que não veio pela linha de comando."""
    owner = args.owner or ask("Owner: ")
    repo = args.repo or ask("Repository: ")
    limit = args.limit
    label = args.label
    if limit is None:
        answer = ask(f"Quantidade [{settings.default_issues}]: ")
        if not answer:
            limit = settings.default_issues
        elif answer.isdigit():
            limit = int(answer)
        else:
            limit = 0
        # A label só é perguntada no modo interativo; Enter coleta todas as issues.
        if label is None:
            label = ask("Label (opcional, ex.: debt): ")
        print()

    if not owner or not repo:
        raise pipeline.PipelineError("owner e repository são obrigatórios.")
    if limit <= 0:
        raise pipeline.PipelineError("a quantidade deve ser um número inteiro maior que zero.")
    return owner, repo, limit, label or None


def run_pipeline(args, settings):
    """Executa o pipeline completo e mostra o resultado."""
    print("DebtRadar — Analisador de Dívida Técnica (1ª etapa: texto)")
    print()
    try:
        if args.file:
            collection, raw_path = pipeline.load(Path(args.file).resolve())
        else:
            owner, repo, limit, label = ask_parameters(args, settings)
            if not settings.has_github_token:
                print("Aviso: sem GITHUB_TOKEN a API permite só 60 requisições por hora.")
            sources = SOURCES if args.source == "all" else (args.source,)
            collection, raw_path = pipeline.collect(owner, repo, limit, label, sources, settings)
        documents, summary = pipeline.analyze(collection, settings)
    except pipeline.PipelineError as error:
        print()
        print(f"Erro: {error}")
        return 1
    except KeyboardInterrupt:
        print()
        print("Execução interrompida.")
        return 130

    processed_path, summary_path = pipeline.save_results(documents, summary, raw_path)
    print_report(summary, [("Coleta", raw_path), ("Documentos", processed_path),
                           ("Resumo", summary_path)])
    return 0


def run_explanation(text, settings):
    """Mostra o que cada etapa faz com um único texto."""
    try:
        result = pipeline.explain(text, settings)
    except pipeline.PipelineError as error:
        print(f"Erro: {error}")
        return 1
    print_explanation(result)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="DebtRadar — análise de dívida técnica em issues do GitHub."
    )
    parser.add_argument("--owner", help="dono ou organização, ex.: microsoft")
    parser.add_argument("--repo", help="nome do repositório, ex.: vscode")
    parser.add_argument("--limit", type=int, help="quantidade de issues")
    parser.add_argument("--label", help="coleta só issues com esta label, ex.: debt")
    parser.add_argument("--source", choices=[*SOURCES, "all"], default="issues",
                        help="o que coletar: issues (padrão), prs, commits ou all")
    parser.add_argument("--text", help="analisa só este texto e mostra cada etapa")
    parser.add_argument("--file", help="analisa uma coleta já salva em data/raw/, sem usar a API")
    parser.add_argument("--check", action="store_true",
                        help="só verifica a configuração e o ambiente")
    return parser


def main():
    args = build_parser().parse_args()
    try:
        settings = config.load_config()
    except config.ConfigError as error:
        print(f"Erro de configuração: {error}")
        print("Corrija o arquivo .env (veja o .env.example) e rode novamente.")
        return 1

    config.ensure_directories()
    if args.check:
        return run_check(settings)
    if args.text is not None:
        return run_explanation(args.text, settings)
    return run_pipeline(args, settings)


if __name__ == "__main__":
    sys.exit(main())
