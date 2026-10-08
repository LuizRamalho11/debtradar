"""Gera docs/etapa1/RESULTADOS.md a partir dos resumos em data/results/.

Todos os números do documento saem dos arquivos de resumo; nada é digitado
à mão. Rode depois de reanalisar as coletas.

Uso:
    python tools/gerar_resultados.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.storage import load_json  # noqa: E402  (precisa do caminho acima)

OUTPUT = ROOT / "docs" / "etapa1" / "RESULTADOS.md"

CATEGORY_NAMES = {"code": "Código", "architecture": "Arquitetura", "tests": "Testes",
                  "documentation": "Documentação", "dependencies": "Dependências"}
SOURCE_NAMES = {"issues": "issues", "prs": "pull requests", "commits": "commits"}

# Labels com que os mantenedores marcam dívida, limpeza ou refatoração.
DEBT_LABELS = {"debt", "kind/cleanup", "Refactor"}
CONTROL_LABELS = {"bug"}


def load_summaries():
    summaries = []
    for path in sorted((ROOT / "data" / "results").glob("*_summary.json")):
        summary = load_json(path)
        summary["file"] = path.name.replace("_summary.json", ".json")
        summaries.append(summary)
    return summaries


def describe_source(metadata):
    sources = metadata.get("sources", ["issues"])
    return " + ".join(SOURCE_NAMES[name] for name in sources)


def repository(metadata):
    return f"{metadata['owner']}/{metadata['repo']}"


def percent(part, total):
    return f"{100 * part / total:.0f}%" if total else "-"


def days(value):
    return "-" if value is None else f"{value:.1f}".replace(".", ",")


def top(entries, size):
    return ", ".join(f"{entry['name']} ({entry['count']})" for entry in entries[:size]) or "nenhum"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines


def build():
    summaries = load_summaries()
    lines = [
        "# Resultados da Etapa 1",
        "",
        "Resultados do DebtRadar sobre todas as coletas reais guardadas em",
        "`data/`. Este arquivo é gerado por `python tools/gerar_resultados.py`",
        "a partir dos resumos em `data/results/`; não deve ser editado à mão.",
        "",
        "Para refazer qualquer linha, reanalise a coleta correspondente:",
        "",
        "```bash",
        "python main.py --file data/raw/<arquivo>",
        "```",
        "",
        "## Coletas",
        "",
    ]
    lines += table(
        ["Arquivo em `data/raw/`", "Repositório", "Fonte", "Label", "Coletados", "De bots", "Analisados", "Período"],
        [[f"`{s['file']}`", repository(s["metadata"]), describe_source(s["metadata"]),
          f"`{s['metadata']['label']}`" if s["metadata"]["label"] else "-",
          s["metadata"]["collected"], s["metadata"]["bot_issues_ignored"], s["totals"]["documents"],
          f"{s['totals']['first_date']} a {s['totals']['last_date']}"] for s in summaries])

    total_collected = sum(s["metadata"]["collected"] for s in summaries)
    total_analyzed = sum(s["totals"]["documents"] for s in summaries)
    lines += ["", f"Ao todo, {total_collected} registros coletados e {total_analyzed} analisados, "
                  f"em {len({repository(s['metadata']) for s in summaries})} repositórios. "
                  "Duas coletas do `psf/requests` se sobrepõem: os registros de uma estão também na outra.", ""]

    lines += ["## Dívida técnica identificada", "",
              "\"Dívida identificada\" é ter um padrão explícito da Regex ou ao menos um",
              "tipo confirmado pelas regras.", ""]
    lines += table(
        ["Arquivo", "Analisados", "Padrão explícito", "Tipo confirmado", "Dívida identificada", "Parcela"],
        [[f"`{s['file']}`", s["totals"]["documents"], s["totals"]["explicit_debt_documents"],
          s["totals"]["classified_documents"], s["totals"]["debt_documents"],
          percent(s["totals"]["debt_documents"], s["totals"]["documents"])] for s in summaries])

    lines += ["", "### Por tipo de dívida", "", "Documentos em que cada tipo foi confirmado (`yes`).", ""]
    lines += table(
        ["Arquivo"] + list(CATEGORY_NAMES.values()),
        [[f"`{s['file']}`"] + [s["classification"][name]["yes"] for name in CATEGORY_NAMES]
         for s in summaries])

    mixed = [s for s in summaries if len(s["by_type"]) > 1]
    if mixed:
        lines += ["", "### Por fonte, nas coletas com mais de uma", ""]
        rows = []
        for s in mixed:
            for name, entry in s["by_type"].items():
                rows.append([f"`{s['file']}`", name, entry["documents"], entry["debt_documents"]])
        lines += table(["Arquivo", "Tipo de registro", "Analisados", "Dívida identificada"], rows)

    lines += ["", "## Validação com as labels dos mantenedores", "",
              "Não há gabarito do tipo de dívida. A referência disponível são as labels",
              "que os mantenedores deram às issues e aos pull requests.", ""]
    rows = []
    totals = {"issues": [0, 0], "prs": [0, 0]}
    control = []
    for s in summaries:
        metadata = s["metadata"]
        sources = metadata.get("sources", ["issues"])
        if metadata["label"] in DEBT_LABELS and len(sources) == 1 and sources[0] in totals:
            kind = sources[0]
            totals[kind][0] += s["totals"]["documents"]
            totals[kind][1] += s["totals"]["debt_documents"]
            rows.append([repository(metadata), SOURCE_NAMES[kind], f"`{metadata['label']}`",
                         s["totals"]["documents"], s["totals"]["debt_documents"],
                         percent(s["totals"]["debt_documents"], s["totals"]["documents"])])
        elif metadata["label"] in CONTROL_LABELS:
            control.append(s)
    lines += table(["Repositório", "Fonte", "Label", "Analisados", "Dívida identificada", "Parcela"], rows)
    lines.append("")
    for kind, (analyzed, found) in totals.items():
        if analyzed:
            lines.append(f"- **{SOURCE_NAMES[kind].capitalize()} rotulados como dívida:** "
                         f"{found} de {analyzed} identificados ({percent(found, analyzed)}).")
    for s in control:
        lines.append(f"- **Grupo de controle** (`{repository(s['metadata'])}`, label "
                     f"`{s['metadata']['label']}`): {s['totals']['debt_documents']} de "
                     f"{s['totals']['documents']} marcados.")
    lines += ["", "Esses números não são acurácia: dizem quanto do que os mantenedores",
              "rotularam o programa encontra, e não se o tipo atribuído está certo.", ""]

    lines += ["## Sentimento", "", "Rótulo de cada documento, pela média do `compound` das sentenças.", ""]
    lines += table(
        ["Arquivo", "Positivos", "Neutros", "Negativos", "Média do compound"],
        [[f"`{s['file']}`", s["sentiment"]["overall"]["positive"], s["sentiment"]["overall"]["neutral"],
          s["sentiment"]["overall"]["negative"],
          f"{s['sentiment']['overall']['mean_compound']:+.3f}".replace(".", ",")] for s in summaries])

    lines += ["", "## Resolução", "",
              "Issues e pull requests com e sem dívida identificada: quantos foram",
              "fechados e a mediana de dias até o fechamento. É um indício de",
              "priorização, não uma medida. Coletas só de commits não aparecem.", ""]
    rows = []
    for s in summaries:
        with_debt, without = s["resolution"]["with_debt"], s["resolution"]["without_debt"]
        if with_debt["documents"] + without["documents"] == 0:
            continue
        rows.append([f"`{s['file']}`",
                     f"{with_debt['closed']} de {with_debt['documents']}", days(with_debt["median_days_to_close"]),
                     f"{without['closed']} de {without['documents']}", days(without["median_days_to_close"])])
    lines += table(["Arquivo", "Com dívida: fechados", "Mediana (dias)", "Sem dívida: fechados", "Mediana (dias)"], rows)

    lines += ["", "## Termos, tecnologias e padrões mais frequentes", "",
              "Entre parênteses, o total de ocorrências no corpus.", ""]
    for s in summaries:
        frequencies = s["frequencies"]
        lines += [f"### `{s['file']}`", "",
                  f"- **Substantivos:** {top(frequencies['terms']['noun'], 6)}",
                  f"- **Verbos:** {top(frequencies['terms']['verb'], 6)}",
                  f"- **Expressões:** {top(frequencies['noun_phrases'], 4)}",
                  f"- **Tecnologias (lista do projeto):** {top(frequencies['technologies'], 6)}",
                  f"- **Entidades (NER do modelo):** {top(frequencies['entities'], 5)}",
                  f"- **Padrões de Regex:** {top(frequencies['regex_patterns'], 6)}",
                  f"- **Tokens:** {s['totals']['tokens']} em {s['totals']['sentences']} sentenças", ""]

    text = "\n".join(lines).rstrip() + "\n"
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"{OUTPUT.relative_to(ROOT)}: {len(text.splitlines())} linhas, {len(summaries)} coletas")


if __name__ == "__main__":
    build()
