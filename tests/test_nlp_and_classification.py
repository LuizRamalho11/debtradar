"""spaCy, tecnologias, classificação e sentimento."""
from src.debt_classifier import classify_document, decide
from src.nlp_analyzer import analyze_doc
from src.regex_analyzer import analyze_document
from src.sentiment_analyzer import SentimentAnalyzer, split_sentences
from src.technology_analyzer import TechnologyAnalyzer


def analyze(nlp, text):
    """Documento mínimo com as chaves que o classificador usa."""
    return {"regex": analyze_document(text), "nlp": analyze_doc(nlp(text))}


def technologies(nlp, text):
    return {tech["name"]: tech["count"] for tech in TechnologyAnalyzer(nlp).find(nlp(text))}


# --- spaCy ---------------------------------------------------------------

def test_lemmas_group_word_forms_and_skip_stopwords(nlp):
    result = analyze_doc(nlp("We removed the widget. They are removing the widgets."))
    assert result["lemmas"]["verb"] == {"remove": 2}
    assert result["lemmas"]["noun"] == {"widget": 2}
    assert result["sentences"] == 2


def test_code_identifiers_stay_out_of_frequencies(nlp):
    lemmas = analyze_doc(nlp("The runInTerminalHelper function handles paths."))["lemmas"]
    assert "runinterminalhelper" not in {**lemmas["noun"], **lemmas["verb"], **lemmas["adjective"]}


def test_blank_line_ends_the_sentence(nlp):
    assert analyze_doc(nlp("Problem\n\nThe parser is slow"))["sentences"] == 2


def test_numeric_entities_are_discarded(nlp):
    entities = analyze_doc(nlp("Related to #330566 and 16px margins."))["entities"]
    assert not any(any(char.isdigit() for char in entity["text"]) for entity in entities)


def test_empty_document(nlp):
    result = analyze_doc(nlp(""))
    assert result["tokens"] == 0 and result["entities"] == []


# --- Tecnologias ---------------------------------------------------------

def test_required_technologies_are_found(nlp):
    text = ("We use Python, JavaScript, TypeScript, Java, C++, React, Angular, Vue, Node.js, "
            "Django, Spring, Docker, Kubernetes, PostgreSQL, MySQL and MongoDB.")
    assert set(technologies(nlp, text)) == {
        "Python", "JavaScript", "TypeScript", "Java", "C++", "React", "Angular", "Vue",
        "Node.js", "Django", "Spring", "Docker", "Kubernetes", "PostgreSQL", "MySQL", "MongoDB"}


def test_java_is_not_found_inside_javascript(nlp):
    assert technologies(nlp, "JavaScript and javascript only") == {"JavaScript": 2}


def test_aliases_and_lowercase(nlp):
    assert technologies(nlp, "postgres, k8s, nodejs, golang and mysql") == {
        "PostgreSQL": 1, "Kubernetes": 1, "Node.js": 1, "Go": 1, "MySQL": 1}


def test_ambiguous_names_need_exact_spelling(nlp):
    assert technologies(nlp, "The UI should react to changes in the spring. Go to the windows.") == {}


def test_names_joined_by_a_slash(nlp):
    # Defeito real do tokenizador: "C++/Rust" e "Node.js/Electron" são um token só.
    assert technologies(nlp, "Rewrite it in C++/Rust with Node.js/Electron.") == {
        "C++": 1, "Rust": 1, "Node.js": 1, "Electron": 1}
    assert technologies(nlp, "See src/vs/base/common/git.ts and Python/Java.") == {
        "Python": 1, "Java": 1}


def test_overlapping_names_count_once(nlp):
    assert technologies(nlp, "Spring Boot and Visual Studio Code") == {"Spring": 1, "VS Code": 1}


# --- Classificação -------------------------------------------------------

def test_decision_rule():
    assert decide(strong=1, weak=0) == "yes"
    assert decide(strong=0, weak=3) == "yes"
    assert decide(strong=0, weak=2) == "possible"
    assert decide(strong=0, weak=0) == "no"


def test_example_from_the_assignment(nlp):
    result = classify_document(analyze(nlp, "Authentication needs refactoring and has no tests."))
    assert result["categories"] == {
        "code": "yes", "architecture": "possible", "tests": "yes",
        "documentation": "no", "dependencies": "no"}
    assert result["evidence"]["tests"]["patterns"] == {"missing_tests": 1}


def test_deprecated_alone_is_not_a_dependency_issue(nlp):
    # Defeito real: "deprecated patterns" contava como dívida de dependências.
    result = classify_document(analyze(nlp, "Remove the deprecated patterns and outdated titles."))
    assert result["categories"]["dependencies"] == "no"


def test_text_without_debt_vocabulary(nlp):
    result = classify_document(analyze(nlp, "It would be nice to have a dark mode."))
    assert set(result["categories"].values()) == {"no"}


# --- Sentimento ----------------------------------------------------------

def test_sentiment_labels():
    analyzer = SentimentAnalyzer()
    assert analyzer.analyze("This is great, I love it.")["label"] == "positive"
    assert analyzer.analyze("This is terrible and frustrating.")["label"] == "negative"
    assert analyzer.analyze("The function returns a list.")["label"] == "neutral"


def test_technical_terms_carry_no_sentiment():
    # Defeito real: "shared", "approval" e "kill" distorciam a pontuação.
    analyzer = SentimentAnalyzer()
    text = "The shared state needs approval before we kill the process and track the debt."
    assert analyzer.analyze(text)["compound"] == 0.0


def test_no_is_neutral_but_still_negates():
    analyzer = SentimentAnalyzer()
    assert analyzer.analyze("There are no tests for this module.")["compound"] == 0.0
    assert analyzer.analyze("This is no good.")["label"] == "negative"


def test_score_is_averaged_over_sentences():
    result = SentimentAnalyzer().analyze("This is great.\nThe function returns a list.")
    assert result["sentences"] == 2
    assert result["positive_sentences"] == 1 and result["neutral_sentences"] == 1
    assert 0 < result["compound"] < 0.5


def test_sentence_splitting_and_empty_text():
    assert split_sentences("One. Two!\nThree") == ["One.", "Two!", "Three"]
    assert SentimentAnalyzer().analyze("")["label"] == "neutral"
