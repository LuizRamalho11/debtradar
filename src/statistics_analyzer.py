"""Estatísticas do corpus: frequências, sentimento e evolução temporal.

Recebe os documentos já analisados (Regex, spaCy, classificação e
sentimento) e monta um único resumo, que o programa principal exibe e
grava em disco.

Em toda lista de frequência cada item traz:
    count     -> total de ocorrências no corpus;
    documents -> em quantos documentos o item aparece.
Os dois números importam: um termo pode ter muitas ocorrências por
aparecer repetidamente em um único documento.
"""
import statistics
from datetime import datetime, timezone

from src.debt_classifier import CATEGORIES

TOP_TERMS = 20

# Tipos de registro e o nome de cada um, no singular e no plural.
TYPE_NAMES = {
    "issue": ("issue", "issues"),
    "pull_request": ("pull request", "pull requests"),
    "commit": ("commit", "commits"),
}
SENTIMENT_LABELS = ["positive", "neutral", "negative"]
STATUSES = ["yes", "possible", "no"]


def rank(documents, counts_of, limit=None):
    """Soma contagens de todos os documentos e devolve o ranking.

    'counts_of' recebe um documento e devolve um dicionário
    {item: (contagem, dados extras)}; os dados extras (por exemplo a
    categoria de uma tecnologia) são copiados para o resultado.
    """
    totals = {}
    for document in documents:
        for name, (count, extra) in counts_of(document).items():
            entry = totals.setdefault(name, {"name": name, **extra, "count": 0, "documents": 0})
            entry["count"] += count
            entry["documents"] += 1
    ranking = sorted(totals.values(), key=lambda entry: (-entry["count"], entry["name"]))
    return ranking[:limit] if limit else ranking


def term_frequencies(documents):
    """Lemas mais frequentes por classe gramatical e expressões nominais."""
    terms = {
        group: rank(documents,
                    lambda doc, group=group: {lemma: (count, {}) for lemma, count
                                              in doc["nlp"]["lemmas"][group].items()},
                    TOP_TERMS)
        for group in ("noun", "adjective", "verb")
    }
    noun_phrases = rank(documents,
                        lambda doc: {phrase: (count, {}) for phrase, count
                                     in doc["nlp"]["noun_phrases"].items()},
                        TOP_TERMS)
    return terms, noun_phrases


def technology_frequencies(documents):
    return rank(documents, lambda doc: {
        tech["name"]: (tech["count"], {"category": tech["category"]})
        for tech in doc["technologies"]
    })


def entity_frequencies(documents):
    """Entidades do NER; o mesmo texto com rótulos diferentes conta separado."""
    return rank(documents, lambda doc: {
        f"{entity['text']} [{entity['label']}]":
            (entity["count"], {"text": entity["text"], "label": entity["label"]})
        for entity in doc["nlp"]["entities"]
    }, TOP_TERMS)


def pattern_frequencies(documents):
    def counts_of(doc):
        categories = {match["pattern"]: match["category"] for match in doc["regex"]["matches"]}
        return {name: (count, {"category": categories[name]})
                for name, count in doc["regex"]["patterns"].items()}
    return rank(documents, counts_of)


def classification_counts(documents):
    """Para cada categoria, quantos documentos ficaram em yes/possible/no."""
    counts = {category: dict.fromkeys(STATUSES, 0) for category in CATEGORIES}
    for document in documents:
        for category, status in document["classification"]["categories"].items():
            counts[category][status] += 1
    return counts


def sentiment_counts(documents):
    """Distribuição dos rótulos de sentimento e média do compound."""
    counts = dict.fromkeys(SENTIMENT_LABELS, 0)
    for document in documents:
        counts[document["sentiment"]["label"]] += 1
    compounds = [document["sentiment"]["compound"] for document in documents]
    mean = sum(compounds) / len(compounds) if compounds else 0.0
    return {"documents": len(documents), **counts, "mean_compound": round(mean, 4)}


def has_category(document, category):
    return document["classification"]["categories"][category] == "yes"


def has_debt(document):
    """Dívida identificada: marcador explícito da Regex ou algum tipo confirmado."""
    return document["regex"]["technical_debt_detected"] or any(
        has_category(document, category) for category in CATEGORIES)


def counts_by_type(documents):
    """Quantos documentos de cada tipo, e em quantos há dívida identificada."""
    counts = {}
    for name in TYPE_NAMES:
        group = [doc for doc in documents if doc["type"] == name]
        if group:
            counts[name] = {"documents": len(group),
                            "debt_documents": sum(1 for doc in group if has_debt(doc))}
    return counts


def days_to_close(document):
    """Dias entre a criação e o fechamento; None se o registro não foi fechado."""
    if document["state"] != "closed" or not document["closed_at"]:
        return None
    try:
        created = datetime.fromisoformat(document["created_at"].replace("Z", "+00:00"))
        closed = datetime.fromisoformat(document["closed_at"].replace("Z", "+00:00"))
    except ValueError:
        return None
    return (closed - created).total_seconds() / 86400


def resolution(documents):
    """Fechamento de issues e pull requests, com e sem dívida identificada.

    É um indício de priorização, não uma medida: mostra quanto de cada
    grupo já foi fechado e em quanto tempo. Commits não têm estado e
    ficam de fora.
    """
    groups = {"with_debt": [], "without_debt": []}
    for document in documents:
        if document["state"]:
            groups["with_debt" if has_debt(document) else "without_debt"].append(document)

    result = {}
    for name, group in groups.items():
        days = [value for value in map(days_to_close, group) if value is not None]
        result[name] = {
            "documents": len(group),
            "closed": len(days),
            "median_days_to_close": round(statistics.median(days), 1) if days else None,
        }
    return result


def timeline(documents):
    """Contagens por mês de criação da issue (campo created_at da API)."""
    months = {}
    for document in documents:
        month = document["created_at"][:7] or "unknown"  # "2026-09-21T..." -> "2026-09"
        months.setdefault(month, []).append(document)
    return [
        {
            "month": month,
            "documents": len(group),
            "debt_documents": sum(1 for doc in group if has_debt(doc)),
            "explicit_debt": sum(1 for doc in group if doc["regex"]["technical_debt_detected"]),
            "categories": {category: sum(1 for doc in group if has_category(doc, category))
                           for category in CATEGORIES},
            "mean_compound": sentiment_counts(group)["mean_compound"],
        }
        for month, group in sorted(months.items())
    ]


def build_summary(documents, metadata):
    """Monta o resultado consolidado do corpus."""
    classification = classification_counts(documents)
    terms, noun_phrases = term_frequencies(documents)
    dates = sorted(doc["created_at"][:10] for doc in documents if doc["created_at"])
    debt_categories = sorted(
        ({"name": category, **classification[category]} for category in CATEGORIES),
        key=lambda entry: (-entry["yes"], -entry["possible"]),
    )

    return {
        "metadata": {
            **metadata,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "totals": {
            "documents": len(documents),
            "debt_documents": sum(1 for doc in documents if has_debt(doc)),
            "tokens": sum(doc["nlp"]["tokens"] for doc in documents),
            "sentences": sum(doc["nlp"]["sentences"] for doc in documents),
            "explicit_debt_documents": sum(
                1 for doc in documents if doc["regex"]["technical_debt_detected"]),
            "classified_documents": sum(
                1 for doc in documents
                if any(has_category(doc, category) for category in CATEGORIES)),
            "first_date": dates[0] if dates else "",
            "last_date": dates[-1] if dates else "",
        },
        "by_type": counts_by_type(documents),
        "classification": classification,
        "resolution": resolution(documents),
        "sentiment": {
            "overall": sentiment_counts(documents),
            "by_category": {
                category: sentiment_counts(
                    [doc for doc in documents if has_category(doc, category)])
                for category in CATEGORIES
            },
        },
        "frequencies": {
            "terms": terms,
            "noun_phrases": noun_phrases,
            "technologies": technology_frequencies(documents),
            "entities": entity_frequencies(documents),
            "regex_patterns": pattern_frequencies(documents),
            "debt_categories": debt_categories,
        },
        "timeline": timeline(documents),
    }
