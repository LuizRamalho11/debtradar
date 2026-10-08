"""Regex: cada padrão casa o que deve e evita os falsos positivos conhecidos."""
import pytest

from src.regex_analyzer import analyze_document


def patterns(text, code=""):
    return [match["pattern"] for match in analyze_document(text, code)["matches"]]


@pytest.mark.parametrize("text, expected", [
    ("TODO: fix this", "todo"),
    ("carry TODO comments", "todo"),
    ("todo: fix later", "todo"),
    ("// Todo(john): x", "todo"),
    ("FIXME handle null", "fixme"),
    ("XXX revisit", "xxx"),
    ("HACK: bypass", "hack"),
    ("this is hacky", "hack"),
    ("technical debt", "technical_debt"),
    ("Tech Debt", "technical_debt"),
    ("technical-debt", "technical_debt"),
    ("known debt", "debt"),
    ("Refactoring", "refactor"),
    ("legacy code", "legacy_code"),
    ("work-around", "workaround"),
    ("duplicated code", "duplicate_code"),
    ("code smells", "code_smell"),
    ("messy code", "messy_code"),
    ("design debt", "design_debt"),
    ("tightly-coupled", "tightly_coupled"),
    ("Architectural", "architecture"),
    ("redesigned", "redesign"),
    ("test debt", "test_debt"),
    ("no unit tests", "missing_tests"),
    ("flaky tests", "flaky_test"),
    ("test coverage", "test_coverage"),
    ("integration test", "integration_test"),
    ("missing docs", "missing_documentation"),
    ("undocumented", "undocumented"),
    ("updating the documentation", "update_docs"),
    ("old dependencies", "outdated_dependency"),
    ("vulnerable dependency", "vulnerable_dependency"),
    ("deprecated dependency", "deprecated_dependency"),
    ("dependency update", "dependency_update"),
    ("upgrading the dependencies", "upgrade_dependency"),
])
def test_pattern_matches(text, expected):
    assert patterns(text) == [expected]


@pytest.mark.parametrize("text", [
    "Todo",                      # nome de recurso do VS Code (defeito real)
    "tips + todo are similar",
    "todo list",
    "todos os dias",
    "manage_todo_list",
    "hack/README.md",            # pasta hack/ do Kubernetes (defeito real)
    "see ./hack/verify.sh",
    "docs/TODO.md",
    "hackathon",
    "version xxx",
    "xxx.example.com",
    "indebted",
])
def test_known_false_positives_do_not_match_markers(text):
    assert not {"todo", "fixme", "hack", "xxx", "debt"} & set(patterns(text))


def test_search_is_case_insensitive():
    assert patterns("WORKAROUND") == patterns("workaround") == ["workaround"]


def test_same_text_is_counted_once():
    result = analyze_document("We have technical debt and missing documentation.")
    assert result["patterns"] == {"technical_debt": 1, "missing_documentation": 1}


def test_only_explicit_patterns_flag_debt():
    assert analyze_document("The documentation covers the architecture.")["technical_debt_detected"] is False
    assert analyze_document("This needs a refactor.")["technical_debt_detected"] is True


def test_code_blocks_are_searched_only_for_markers():
    result = analyze_document("Plain text.", code="# TODO: drop this\ndocumentation = architecture")
    assert [(m["pattern"], m["source"]) for m in result["matches"]] == [("todo", "code")]


def test_match_positions_point_into_the_text():
    text = "Please refactor this module."
    match = analyze_document(text)["matches"][0]
    assert text[match["start"]:match["end"]] == match["text"] == "refactor"
    assert match["category"] == "general"


def test_empty_text():
    assert analyze_document("") == {
        "technical_debt_detected": False, "patterns": {}, "categories": {}, "matches": []}
