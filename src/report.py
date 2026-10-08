"""Apresentação do resultado consolidado no terminal.

Lê apenas o resumo gerado por statistics_analyzer.build_summary().
"""
import textwrap

from src import config
from src.statistics_analyzer import TYPE_NAMES

WIDTH = 68
BAR_WIDTH = 24
MAX_TIMELINE_ROWS = 12  # acima disso a linha do tempo é mostrada por ano

CATEGORY_NAMES = {
    "code": "Código",
    "architecture": "Arquitetura",
    "tests": "Testes",
    "documentation": "Documentação",
    "dependencies": "Dependências",
}

# Padrões sempre exibidos na seção de Regex, mesmo com zero ocorrências.
MARKERS = [("todo", "TODO"), ("fixme", "FIXME"), ("hack", "HACK"), ("xxx", "XXX")]
EXPRESSIONS = [("technical_debt", "technical debt"), ("debt", "debt"),
               ("refactor", "refactor"), ("legacy_code", "legacy code"),
               ("workaround", "workaround")]


def section(title):
    print()
    print(f"── {title} " + "─" * (WIDTH - len(title) - 4))


def bar(value, maximum):
    """Barra proporcional ao valor; qualquer valor acima de zero aparece."""
    if value <= 0 or maximum <= 0:
        return ""
    return "█" * max(1, round(BAR_WIDTH * value / maximum))


def percent(part, total):
    return f"{100 * part / total:.0f}%" if total else "0%"


def print_items(title, items, separator=", "):
    """Mostra uma lista em uma ou mais linhas, alinhada depois do título."""
    indent = " " * 17
    lines = [""]
    for item in items or ["nenhum"]:
        candidate = lines[-1] + separator + item if lines[-1] else item
        if len(indent) + len(candidate) > WIDTH and lines[-1]:
            # O item não cabe: vai inteiro para a linha seguinte.
            lines[-1] += separator.rstrip()
            lines.append(item)
        else:
            lines[-1] = candidate
    print(f"  {title:15}{lines[0]}")
    for line in lines[1:]:
        print(indent + line)


def ranking(entries, size):
    """Itens de um ranking no formato: nome (ocorrências)."""
    return [f"{entry['name']} ({entry['count']})" for entry in entries[:size]]


def count(number, names):
    """Número com o nome no singular ou no plural: "1 issue", "2 issues"."""
    singular, plural = names
    return f"{number} {singular if number == 1 else plural}"


def relative(path):
    """Caminho a partir da pasta do projeto, quando o arquivo está nela."""
    try:
        return path.relative_to(config.BASE_DIR)
    except ValueError:
        return path


def print_collection(summary):
    metadata = summary["metadata"]
    totals = summary["totals"]
    repository = f"{metadata['owner']}/{metadata['repo']}"
    if metadata["label"]:
        repository += f"  (label: {metadata['label']})"

    section("COLETA")
    print(f"  Repositório           {repository}")
    ignored = metadata["bot_issues_ignored"]
    print(f"  Registros coletados   {metadata['collected']}")
    print(f"  Registros analisados  {totals['documents']}"
          + (f"  ({ignored} de bots, ignorados)" if ignored else ""))
    by_type = summary["by_type"]
    if list(by_type) != ["issue"]:
        sources = ", ".join(count(entry["documents"], TYPE_NAMES[name])
                            for name, entry in by_type.items())
        print(f"  Por fonte             {sources}")
    print(f"  Período               {totals['first_date']} a {totals['last_date']}")
    if metadata["warning"]:
        print(f"  Aviso                 {metadata['warning']}")


def print_debt(summary):
    totals = summary["totals"]
    total = totals["documents"]
    categories = summary["frequencies"]["debt_categories"]
    largest = max(entry["yes"] for entry in categories)

    section("DÍVIDA TÉCNICA")
    print(f"  Total identificado    {totals['debt_documents']} de {total} "
          f"({percent(totals['debt_documents'], total)})")
    print(f"    com marcador explícito (Regex)   {totals['explicit_debt_documents']}")
    print(f"    com tipo confirmado (regras)     {totals['classified_documents']}")
    by_type = summary["by_type"]
    if len(by_type) > 1:
        for name, entry in by_type.items():
            print(f"    em {TYPE_NAMES[name][1]:30}{entry['debt_documents']} de {entry['documents']}")
    print()
    print(f"  {'Categoria':14}{'Sim':>4}{'Possível':>10}")
    for entry in categories:
        print(f"  {CATEGORY_NAMES[entry['name']]:14}{entry['yes']:>4}{entry['possible']:>10}"
              f"  {bar(entry['yes'], largest)}")


def print_regex(summary):
    patterns = {entry["name"]: entry for entry in summary["frequencies"]["regex_patterns"]}

    def cell(name, title):
        entry = patterns.get(name, {"count": 0, "documents": 0})
        return f"{title} {entry['count']}/{entry['documents']}"

    shown = {name for name, _ in MARKERS + EXPRESSIONS}
    others = [entry for entry in summary["frequencies"]["regex_patterns"]
              if entry["name"] not in shown][:5]

    section("REGEX  (ocorrências/documentos)")
    print_items("Marcadores", [cell(name, title) for name, title in MARKERS], "   ")
    print_items("Expressões", [cell(name, title) for name, title in EXPRESSIONS], "   ")
    print_items("Outros", [cell(entry["name"], entry["name"]) for entry in others], "   ")


def print_spacy(summary):
    totals = summary["totals"]
    frequencies = summary["frequencies"]

    section("SPACY")
    print(f"  {'Tokens':15}{totals['tokens']} em {totals['sentences']} sentenças")
    print_items("Substantivos", ranking(frequencies["terms"]["noun"], 6))
    print_items("Verbos", ranking(frequencies["terms"]["verb"], 6))
    print_items("Expressões", ranking(frequencies["noun_phrases"], 4))
    print_items("Entidades NER", ranking(frequencies["entities"], 5))


def print_technologies(summary):
    technologies = summary["frequencies"]["technologies"]

    section("TECNOLOGIAS  (lista do projeto, não é NER)")
    if not technologies:
        print("  Nenhuma tecnologia da lista foi encontrada.")
        return
    largest = technologies[0]["count"]
    for entry in technologies[:8]:
        print(f"  {entry['name']:12}{entry['count']:>4}  {bar(entry['count'], largest)}")
    if len(technologies) > 8:
        print(f"  ... e mais {len(technologies) - 8}")


def print_sentiment(summary):
    overall = summary["sentiment"]["overall"]
    total = overall["documents"]
    largest = max(overall[label] for label in ("positive", "neutral", "negative"))

    section("SENTIMENTO  (tom do texto; não mede a dívida)")
    for label, title in (("positive", "Positivo"), ("neutral", "Neutro"), ("negative", "Negativo")):
        print(f"  {title:9}{overall[label]:>4}  {percent(overall[label], total):>4}"
              f"  {bar(overall[label], largest)}")
    print(f"  Média do compound: {overall['mean_compound']:+.3f}  (escala de -1 a +1)")


def print_resolution(summary):
    groups = summary["resolution"]
    if not any(group["documents"] for group in groups.values()):
        return  # só commits: não há o que fechar

    section("RESOLUÇÃO  (indício de priorização; issues e pull requests)")
    print(f"  {'Grupo':12}{'Total':>6}{'Fechadas':>10}{'Mediana até fechar':>21}")
    for name, title in (("with_debt", "Com dívida"), ("without_debt", "Sem dívida")):
        group = groups[name]
        median = group["median_days_to_close"]
        days = "-" if median is None else f"{median:.1f} dias".replace(".", ",")
        print(f"  {title:12}{group['documents']:>6}{group['closed']:>10}{days:>21}")


def group_by_year(months):
    """Soma os meses de cada ano, para períodos longos caberem na tela."""
    years = {}
    for month in months:
        name = month["month"][:4]
        year = years.setdefault(name, {"month": name, "documents": 0, "debt_documents": 0})
        year["documents"] += month["documents"]
        year["debt_documents"] += month["debt_documents"]
    return list(years.values())


def print_timeline(summary):
    periods, unit = summary["timeline"], "mês"
    if len(periods) > MAX_TIMELINE_ROWS:
        periods, unit = group_by_year(periods), "ano"
    largest = max(period["documents"] for period in periods)

    section(f"TEMPO  (registros por {unit} de criação)")
    print(f"  {unit.capitalize():9}{'Total':>6}{'Com dívida':>12}")
    for period in periods:
        print(f"  {period['month']:9}{period['documents']:>6}{period['debt_documents']:>12}"
              f"  {bar(period['documents'], largest)}")


def print_explanation(result):
    """Mostra, etapa por etapa, a análise de um único texto (opção --text)."""
    section("1. TEXTO LIMPO")
    for line in textwrap.wrap(result["text"] or "(vazio)", WIDTH - 2):
        print(f"  {line}")
    if result["code"]:
        print(f"  Código separado: {textwrap.shorten(result['code'], WIDTH - 20)}")

    section("2. REGEX")
    for match in result["regex"]["matches"]:
        level = "explícito" if match["explicit"] else "contexto"
        print(f"  {match['pattern']:22}{match['category']:15}{level:10} \"{match['text']}\"")
    if not result["regex"]["matches"]:
        print("  Nenhum padrão encontrado.")

    section("3. SPACY  (token, lema, classe gramatical)")
    print(f"  {'token':18}{'lema':18}{'classe':8}{'stopword':10}conta?")
    for token in result["tokens"][:30]:
        print(f"  {token['text'][:17]:18}{token['lemma'][:17]:18}{token['pos']:8}"
              f"{'sim' if token['stopword'] else 'não':10}{'sim' if token['relevant'] else 'não'}")
    if len(result["tokens"]) > 30:
        print(f"  ... e mais {len(result['tokens']) - 30} tokens")
    print_items("Tecnologias", [tech["name"] for tech in result["technologies"]])

    section("4. CLASSIFICAÇÃO  (regras)")
    status_names = {"yes": "SIM", "possible": "possível", "no": "não"}
    for category, status in result["classification"]["categories"].items():
        evidence = result["classification"]["evidence"][category]
        reasons = list(evidence["patterns"]) + [f"{term}×{times}"
                                               for term, times in evidence["terms"].items()]
        print(f"  {CATEGORY_NAMES[category]:14}{status_names[status]:10}{', '.join(reasons)}")

    section("5. SENTIMENTO")
    sentiment = result["sentiment"]
    label = {"positive": "positivo", "neutral": "neutro", "negative": "negativo"}[sentiment["label"]]
    print(f"  {label} (compound {sentiment['compound']:+.3f}, "
          f"média de {count(sentiment['sentences'], ('sentença', 'sentenças'))})")
    print()


def print_report(summary, files):
    """Mostra o resultado completo. 'files' são os arquivos gravados."""
    metadata = summary["metadata"]
    print()
    print("═" * WIDTH)
    print(f" DebtRadar — resultado de {metadata['owner']}/{metadata['repo']}")
    print("═" * WIDTH)

    print_collection(summary)
    print_debt(summary)
    print_regex(summary)
    print_spacy(summary)
    print_technologies(summary)
    print_sentiment(summary)
    print_resolution(summary)
    print_timeline(summary)

    section("ARQUIVOS")
    for title, path in files:
        print(f"  {title:11}{relative(path)}")
    print()
