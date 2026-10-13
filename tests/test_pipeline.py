"""Pipeline completo sobre uma coleta pequena, sem acessar a rede."""
import pytest

from src import config, pipeline
from src.report import print_report
from src.storage import load_json, save_json


@pytest.fixture
def settings():
    return config.Config(github_token="", spacy_model=config.DEFAULT_SPACY_MODEL, default_issues=100)


def test_full_pipeline(sample_collection, settings, nlp, data_dirs, capsys):
    raw_path = config.RAW_DIR / "acme_app_debt_issues.json"
    save_json(sample_collection, raw_path)

    collection, loaded_path = pipeline.load(raw_path)
    documents, summary = pipeline.analyze(collection, settings)
    processed_path, summary_path = pipeline.save_results(documents, summary, loaded_path)

    # A issue criada por bot fica de fora, assim como o comentário de bot.
    assert [document["number"] for document in documents] == [1, 2, 3]
    assert summary["metadata"]["bot_issues_ignored"] == 1
    assert documents[0]["bot_comments_ignored"] == 1
    assert "technical debt" not in documents[0]["text"]

    # Cada etapa deixou a sua chave no documento.
    for document in documents:
        assert {"regex", "nlp", "technologies", "classification", "sentiment"} <= set(document)

    first, second, third = documents
    assert first["classification"]["categories"]["code"] == "yes"
    assert first["classification"]["categories"]["tests"] == "yes"
    assert first["regex"]["patterns"]["todo"] == 1          # marcador dentro do bloco de código
    assert second["classification"]["categories"]["dependencies"] == "yes"
    assert {tech["name"] for tech in second["technologies"]} == {"Python", "Django"}
    assert third["regex"]["technical_debt_detected"] is False

    # O resumo é coerente com os documentos.
    totals = summary["totals"]
    assert totals["documents"] == 3
    assert totals["debt_documents"] == 2
    assert all(sum(counts.values()) == 3 for counts in summary["classification"].values())
    overall = summary["sentiment"]["overall"]
    assert overall["positive"] + overall["neutral"] + overall["negative"] == 3
    assert [(month["month"], month["documents"], month["debt_documents"])
            for month in summary["timeline"]] == [("2026-08", 1, 1), ("2026-09", 2, 1)]

    # Os arquivos gravados podem ser lidos de volta.
    assert load_json(processed_path)["documents"][0]["number"] == 1
    assert load_json(summary_path)["totals"] == totals

    # O relatório mostra os sete blocos e cabe em 80 colunas.
    capsys.readouterr()
    print_report(summary, [("Coleta", raw_path)])
    output = capsys.readouterr().out
    for title in ("COLETA", "DÍVIDA TÉCNICA", "REGEX", "SPACY", "TECNOLOGIAS", "SENTIMENTO", "TEMPO"):
        assert f"── {title}" in output
    assert "1 de bots, ignorados" in output
    report_body = output.split("── ARQUIVOS")[0]  # os caminhos dos arquivos podem ser longos
    assert max(len(line) for line in report_body.splitlines()) <= 80


def test_sources_and_resolution_in_the_summary(sample_collection, settings, nlp, capsys):
    from tests.conftest import make_issue
    sample_collection["issues"] = [
        make_issue(1, "Refactor the parser", "This hack needs a refactor.",
                   closed_at="2026-08-14T12:00:00Z"),                      # dívida, 4 dias
        make_issue(2, "Dark mode", "It would be nice.", closed_at="2026-08-11T12:00:00Z"),  # 1 dia
        make_issue(3, "Add an avatar", "Small feature."),                   # aberta
        make_issue(4, "Remove duplicated code", "TODO: drop the legacy code.", kind="pull_request",
                   closed_at="2026-08-12T12:00:00Z"),                      # dívida, 2 dias
        make_issue(5, "Fix typo", "", kind="commit"),
        make_issue(6, "Workaround for the flaky tests", "", kind="commit"),  # dívida
    ]
    documents, summary = pipeline.analyze(sample_collection, settings)

    assert [document["type"] for document in documents] == [
        "issue", "issue", "issue", "pull_request", "commit", "commit"]
    assert summary["by_type"] == {
        "issue": {"documents": 3, "debt_documents": 1},
        "pull_request": {"documents": 1, "debt_documents": 1},
        "commit": {"documents": 2, "debt_documents": 1},
    }
    # Commits não têm estado e não entram na resolução.
    assert summary["resolution"] == {
        "with_debt": {"documents": 2, "closed": 2, "median_days_to_close": 3.0},
        "without_debt": {"documents": 2, "closed": 1, "median_days_to_close": 1.0},
    }

    capsys.readouterr()
    print_report(summary, [])
    output = capsys.readouterr().out
    assert "3 issues, 1 pull request, 2 commits" in output
    assert "em issues" in output and "1 de 3" in output and "em commits" in output
    assert "── RESOLUÇÃO" in output and "3,0 dias" in output


def test_old_collections_without_type_are_issues(sample_collection, settings, nlp):
    for issue in sample_collection["issues"]:
        del issue["type"], issue["id"]
    documents, summary = pipeline.analyze(sample_collection, settings)
    assert {document["type"] for document in documents} == {"issue"}
    assert documents[0]["id"] == "#1"
    assert list(summary["by_type"]) == ["issue"]


def test_explain_a_single_text(settings, nlp, capsys):
    from src.report import print_explanation
    result = pipeline.explain(
        "**Authentication** needs refactoring and has no tests. We use Django.", settings)
    assert result["text"] == "Authentication needs refactoring and has no tests. We use Django."
    assert [match["pattern"] for match in result["regex"]["matches"]] == ["refactor", "missing_tests"]
    assert result["tokens"][0] == {"text": "Authentication", "lemma": "authentication",
                                   "pos": "NOUN", "stopword": False, "relevant": True}
    assert [tech["name"] for tech in result["technologies"]] == ["Django"]
    assert result["classification"]["categories"]["code"] == "yes"
    assert result["classification"]["categories"]["architecture"] == "possible"
    assert result["classification"]["categories"]["tests"] == "yes"

    print_explanation(result)
    output = capsys.readouterr().out
    for title in ("1. TEXTO LIMPO", "2. REGEX", "3. SPACY", "4. CLASSIFICAÇÃO", "5. SENTIMENTO"):
        assert title in output
    assert max(len(line) for line in output.splitlines()) <= 80


def test_long_periods_are_shown_by_year():
    from src.report import group_by_year
    months = [{"month": "2023-07", "documents": 1, "debt_documents": 0},
              {"month": "2023-10", "documents": 2, "debt_documents": 1},
              {"month": "2024-01", "documents": 1, "debt_documents": 1}]
    assert group_by_year(months) == [
        {"month": "2023", "documents": 3, "debt_documents": 1},
        {"month": "2024", "documents": 1, "debt_documents": 1}]


def test_load_rejects_missing_and_invalid_files(tmp_path):
    with pytest.raises(pipeline.PipelineError, match="não encontrado"):
        pipeline.load(tmp_path / "missing.json")
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not json", encoding="utf-8")
    with pytest.raises(pipeline.PipelineError, match="não é uma coleta"):
        pipeline.load(invalid)
    save_json({"metadata": {}, "documents": []}, invalid)
    with pytest.raises(pipeline.PipelineError, match="não é uma coleta"):
        pipeline.load(invalid)
    # Defeitos reais: uma pasta ou um arquivo binário terminavam em traceback.
    with pytest.raises(pipeline.PipelineError, match="Não foi possível ler"):
        pipeline.load(tmp_path)
    invalid.write_bytes(b"PK\x03\x04\x81\xff binary")
    with pytest.raises(pipeline.PipelineError, match="não é uma coleta"):
        pipeline.load(invalid)


def test_load_rejects_issues_with_missing_fields(tmp_path, sample_collection):
    del sample_collection["issues"][0]["title"]
    path = tmp_path / "incomplete.json"
    save_json(sample_collection, path)
    with pytest.raises(pipeline.PipelineError, match="não é uma coleta"):
        pipeline.load(path)


def test_collection_with_only_bot_issues_is_rejected(sample_collection, settings):
    sample_collection["issues"] = [issue for issue in sample_collection["issues"]
                                   if issue["author"].endswith("[bot]")]
    with pytest.raises(pipeline.PipelineError, match="criados por bots"):
        pipeline.analyze(sample_collection, settings)


def test_empty_collection_says_what_was_searched(settings, data_dirs, monkeypatch):
    class EmptyCollector:
        """A API devolve uma lista vazia, sem erro, para uma label que não existe."""
        def __init__(self, token):
            pass

        def collect(self, owner, repo, limit, label, sources):
            return {"metadata": {}, "issues": []}

    monkeypatch.setattr(pipeline, "GitHubCollector", EmptyCollector)
    with pytest.raises(pipeline.PipelineError) as error:
        pipeline.collect("psf", "requests", 5, "debt", ("issues",), settings)
    message = str(error.value)
    assert 'psf/requests com a label "debt"' in message
    assert "https://github.com/psf/requests/labels" in message
    assert "deixe a label em branco" in message

    with pytest.raises(pipeline.PipelineError) as error:
        pipeline.collect("psf", "requests", 5, None, ("issues",), settings)
    assert "label" not in str(error.value)
    assert not list(config.RAW_DIR.iterdir())        # nada é gravado


def test_missing_spacy_model_has_a_clear_message(sample_collection):
    settings = config.Config(github_token="", spacy_model="modelo_inexistente", default_issues=100)
    with pytest.raises(pipeline.PipelineError, match="spacy download modelo_inexistente"):
        pipeline.analyze(sample_collection, settings)


def test_config_validation(monkeypatch):
    monkeypatch.setenv("DEFAULT_ISSUES", "abc")
    with pytest.raises(config.ConfigError, match="número inteiro"):
        config.load_config()
    monkeypatch.setenv("DEFAULT_ISSUES", "-5")
    with pytest.raises(config.ConfigError, match="maior que zero"):
        config.load_config()
    monkeypatch.setenv("DEFAULT_ISSUES", "25")
    assert config.load_config().default_issues == 25


def test_token_is_not_shown_when_the_config_is_printed(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "valor_secreto")
    settings = config.load_config()
    assert settings.has_github_token
    assert "valor_secreto" not in repr(settings)
