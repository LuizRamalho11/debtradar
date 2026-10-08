"""Classificação do tipo de dívida técnica com regras.

É um baseline baseado em regras e listas de termos: não há aprendizado de
máquina nem treinamento. Para cada categoria o documento recebe um de três
resultados, a partir de dois tipos de evidência já produzidos pelas fases
anteriores:

- evidência forte: padrões explícitos encontrados pela Regex
  (ex.: "no tests", "code smell", "vulnerable dependency");
- evidência fraca: vocabulário do tema, contado pelos lemas do spaCy
  (ex.: "test", "coverage"), em qualquer flexão da palavra.

Regra de decisão:
    "yes"      -> há evidência forte, ou a evidência fraca se repete
                  (YES_THRESHOLD ocorrências ou mais);
    "possible" -> há só um pouco de evidência fraca;
    "no"       -> nenhuma evidência.

Um documento pode pertencer a várias categorias.
"""

CATEGORIES = ["code", "architecture", "tests", "documentation", "dependencies"]

YES_THRESHOLD = 3

# Padrões explícitos da Regex (regex_analyzer.py) que confirmam a categoria.
STRONG_PATTERNS = {
    "code": {"todo", "fixme", "hack", "xxx", "duplicate_code", "code_smell",
             "messy_code", "refactor", "legacy_code", "workaround"},
    "architecture": {"design_debt", "tightly_coupled"},
    "tests": {"test_debt", "missing_tests", "flaky_test"},
    "documentation": {"missing_documentation", "undocumented"},
    "dependencies": {"outdated_dependency", "vulnerable_dependency",
                     "deprecated_dependency"},
}

# Padrões que só sugerem a categoria: refatorar costuma envolver o desenho
# do sistema, mas não necessariamente.
WEAK_PATTERNS = {
    "architecture": {"refactor"},
}

# Vocabulário de cada tema, na forma de lema (como o spaCy devolve).
# Para ampliar a cobertura, basta acrescentar lemas aqui.
TERMS = {
    "code": {"duplicate", "duplication", "cleanup", "simplify", "consolidate",
             "unify", "hardcode", "unused", "obsolete", "legacy"},
    "architecture": {"architecture", "architectural", "coupling", "decouple",
                     "abstraction", "layer", "layering", "modularity",
                     "redesign", "restructure", "monolith"},
    "tests": {"test", "testing", "coverage", "flaky", "smoketest"},
    "documentation": {"documentation", "doc", "readme", "docstring",
                      "undocumented", "wiki"},
    # "deprecated" e "outdated" ficam de fora: sozinhas descrevem qualquer
    # coisa antiga, não só dependências (a Regex cobre "outdated dependency").
    "dependencies": {"dependency", "upgrade", "vulnerable", "vulnerability"},
}


def decide(strong, weak):
    """Aplica a regra de decisão a partir das contagens de evidência."""
    if strong > 0 or weak >= YES_THRESHOLD:
        return "yes"
    if weak > 0:
        return "possible"
    return "no"


def classify_document(document):
    """Classifica um documento já analisado pela Regex e pelo spaCy.

    Devolve o resultado por categoria e a evidência usada em cada decisão.
    """
    patterns = document["regex"]["patterns"]
    lemma_counts = {}
    for group in document["nlp"]["lemmas"].values():
        for lemma, count in group.items():
            lemma_counts[lemma] = lemma_counts.get(lemma, 0) + count

    categories = {}
    evidence = {}
    for category in CATEGORIES:
        strong = {name: patterns[name] for name in sorted(STRONG_PATTERNS[category])
                  if name in patterns}
        weak_patterns = {name: patterns[name]
                         for name in sorted(WEAK_PATTERNS.get(category, ()))
                         if name in patterns}
        terms = {lemma: lemma_counts[lemma] for lemma in sorted(TERMS[category])
                 if lemma in lemma_counts}
        weak = sum(weak_patterns.values()) + sum(terms.values())

        categories[category] = decide(sum(strong.values()), weak)
        evidence[category] = {"patterns": {**strong, **weak_patterns}, "terms": terms}

    return {"categories": categories, "evidence": evidence}
