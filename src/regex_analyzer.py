"""Detecção de dívida técnica com expressões regulares.

Cada padrão tem um nome, uma categoria de dívida e um nível:

- explícito: a expressão por si só aponta um atalho ou problema
  (TODO, "code smell", "missing tests", "vulnerable dependency");
- contexto: palavra neutra que só indica o assunto do texto
  ("architecture", "documentation", "unit test").

Só padrões explícitos marcam o documento como dívida técnica; os de
contexto ajudam a dizer de que tipo de dívida se trata.

Elementos de Regex usados:
    \\b         fronteira de palavra: "hack" não casa dentro de "hackathon"
    (?:a|b)    alternativas sem criar grupo de captura
    s?         caractere opcional (plural)
    \\s+        um ou mais espaços, inclusive quebra de linha
    [\\s-]+     espaço ou hífen: "tech debt" e "tech-debt"
    (?!...)    lookahead negativo: casa só se NÃO vier isso depois
    (?<!...)   lookbehind negativo: casa só se NÃO vier isso antes
    (?=...)    lookahead positivo: casa só se vier isso depois
    (?-i:...)  desliga o "ignorar maiúsculas" só dentro do grupo
"""
import re
from typing import NamedTuple


class DebtPattern(NamedTuple):
    name: str
    category: str
    explicit: bool
    regex: str


CATEGORIES = ["general", "code", "architecture", "tests", "documentation", "dependencies"]

# Marcadores de comentário não podem ser parte de um caminho de arquivo:
# o repositório do Kubernetes tem uma pasta "hack/", e "hack/README.md"
# não é um HACK. O marcador não pode vir depois de letra, "/" ou ".",
# nem ser seguido de letra, "/" ou de uma extensão (".md").
BEFORE_MARKER = r"(?<![\w/.])"
AFTER_MARKER = r"(?![\w/]|\.\w)"


def comment_marker(word):
    """Regex de um marcador de comentário de código (TODO, FIXME, XXX).

    Em maiúsculas o marcador vale sempre. Em minúsculas só vale com a
    sintaxe de marcador ("todo:", "todo(fulano)"), porque "todo" e "xxx"
    também aparecem em texto comum: no VS Code, "todo" é o nome de um
    recurso do produto.
    """
    upper = f"(?-i:{word.upper()})"
    with_syntax = word + r"(?=\s*[:(])"
    return BEFORE_MARKER + f"(?:{upper}|{with_syntax})" + AFTER_MARKER

# Dentro de cada categoria, expressões mais específicas vêm antes das mais
# genéricas: um trecho do texto é contado uma vez só, pelo primeiro padrão
# que o encontrar ("missing documentation" não conta de novo como "documentation").
PATTERNS = [
    # --- Geral ---
    DebtPattern("technical_debt", "general", True, r"\btech(?:nical)?[\s-]+debts?\b"),
    DebtPattern("refactor", "general", True, r"\brefactor(?:s|ed|ing)?\b"),
    DebtPattern("legacy_code", "general", True, r"\blegacy[\s-]+code(?:base)?\b"),
    DebtPattern("workaround", "general", True, r"\bwork[\s-]?arounds?\b"),
    DebtPattern("cleanup", "general", False, r"\bclean[\s-]?ups?\b"),
    DebtPattern("legacy", "general", False, r"\blegacy\b"),

    # --- Código ---
    DebtPattern("todo", "code", True, comment_marker("todo")),
    DebtPattern("fixme", "code", True, comment_marker("fixme")),
    DebtPattern("xxx", "code", True, comment_marker("xxx")),
    # "hack" e "hacky" são vocabulário comum de dívida: valem em qualquer caixa.
    DebtPattern("hack", "code", True,
                BEFORE_MARKER + r"hack(?:s|y|ed|ish)?" + AFTER_MARKER),
    DebtPattern("duplicate_code", "code", True,
                r"\b(?:duplicated?\s+code|code\s+duplication)\b"),
    DebtPattern("code_smell", "code", True, r"\bcode\s+smells?\b"),
    DebtPattern("messy_code", "code", True, r"\bmessy\s+code\b"),
    DebtPattern("duplication", "code", False, r"\bduplicat(?:ed|ion)\b"),

    # --- Arquitetura ---
    DebtPattern("design_debt", "architecture", True, r"\bdesign[\s-]+debt\b"),
    DebtPattern("tightly_coupled", "architecture", True, r"\btightly[\s-]+coupled\b"),
    DebtPattern("architecture", "architecture", False, r"\barchitectur(?:e|al)\b"),
    DebtPattern("coupling", "architecture", False, r"\bcoupling\b"),
    DebtPattern("redesign", "architecture", False, r"\bredesign(?:s|ed|ing)?\b"),

    # --- Testes ---
    DebtPattern("test_debt", "tests", True, r"\btest(?:ing)?[\s-]+debt\b"),
    DebtPattern("missing_tests", "tests", True,
                r"\b(?:missing|no)\s+(?:unit\s+|integration\s+)?tests?\b"),
    DebtPattern("flaky_test", "tests", True, r"\bflaky\s+tests?\b"),
    DebtPattern("test_coverage", "tests", False, r"\b(?:test|code)\s+coverage\b"),
    DebtPattern("unit_test", "tests", False, r"\bunit[\s-]tests?\b"),
    DebtPattern("integration_test", "tests", False, r"\bintegration[\s-]tests?\b"),

    # --- Documentação ---
    DebtPattern("missing_documentation", "documentation", True,
                r"\bmissing\s+(?:documentation|docs)\b"),
    DebtPattern("undocumented", "documentation", True, r"\bundocumented\b"),
    DebtPattern("update_docs", "documentation", False,
                r"\bupdat(?:e|es|ed|ing)\s+(?:the\s+)?(?:documentation|docs)\b"),
    DebtPattern("documentation", "documentation", False, r"\bdocumentation\b"),
    DebtPattern("docs", "documentation", False, r"\bdocs\b"),

    # --- Dependências ---
    DebtPattern("outdated_dependency", "dependencies", True,
                r"\b(?:outdated|old)\s+dependenc(?:y|ies)\b"),
    DebtPattern("vulnerable_dependency", "dependencies", True,
                r"\bvulnerable\s+dependenc(?:y|ies)\b"),
    DebtPattern("deprecated_dependency", "dependencies", True,
                r"\bdeprecated\s+dependenc(?:y|ies)\b"),
    DebtPattern("dependency_update", "dependencies", False,
                r"\bdependenc(?:y|ies)\s+(?:update|upgrade)s?\b"),
    DebtPattern("upgrade_dependency", "dependencies", False,
                r"\b(?:upgrad|updat)(?:e|es|ed|ing)\s+(?:the\s+)?dependenc(?:y|ies)\b"),

    # --- Genérico por último: só conta se nenhum "... debt" acima casou ---
    DebtPattern("debt", "general", True, r"\bdebts?\b"),
]

# A busca ignora maiúsculas e minúsculas; a única exceção são os marcadores
# de comentário, tratados em comment_marker().
COMPILED = [(pattern, re.compile(pattern.regex, re.IGNORECASE)) for pattern in PATTERNS]

# Em blocos de código só interessam os marcadores de comentário.
CODE_MARKERS = {"todo", "fixme", "hack", "xxx"}

CONTEXT_WIDTH = 50  # caracteres mostrados antes e depois de cada ocorrência


def find_matches(content, source, only=None):
    """Procura os padrões em 'content' e devolve as ocorrências em ordem.

    'source' diz de onde veio o conteúdo ("text" ou "code") e 'only'
    restringe a busca a alguns nomes de padrão.
    """
    matches = []
    taken = []  # trechos já contados, para não contar o mesmo duas vezes
    for pattern, regex in COMPILED:
        if only and pattern.name not in only:
            continue
        for found in regex.finditer(content):
            start, end = found.span()
            if any(start < taken_end and taken_start < end for taken_start, taken_end in taken):
                continue
            taken.append((start, end))
            context = content[max(0, start - CONTEXT_WIDTH):end + CONTEXT_WIDTH]
            matches.append({
                "pattern": pattern.name,
                "category": pattern.category,
                "explicit": pattern.explicit,
                "text": found.group(0),
                "source": source,
                "start": start,
                "end": end,
                "context": " ".join(context.split()),
            })
    return sorted(matches, key=lambda match: match["start"])


def count_by(matches, field):
    """Conta as ocorrências por um campo, ex.: 'pattern' ou 'category'."""
    counts = {}
    for match in matches:
        counts[match[field]] = counts.get(match[field], 0) + 1
    return counts


def analyze_document(text, code=""):
    """Analisa um documento e devolve o resultado das Regex."""
    matches = find_matches(text, "text") + find_matches(code, "code", CODE_MARKERS)
    return {
        "technical_debt_detected": any(match["explicit"] for match in matches),
        "patterns": count_by(matches, "pattern"),
        "categories": count_by(matches, "category"),
        "matches": matches,
    }
