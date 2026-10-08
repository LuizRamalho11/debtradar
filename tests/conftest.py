"""Recursos compartilhados pelos testes.

Os testes não acessam a rede: a coleta é testada com respostas simuladas e
o pipeline com uma coleta pequena escrita à mão (SAMPLE_ISSUES).
"""
import pytest

from src import config


def make_issue(number, title, body, author="alice", comments=(), created_at="2026-08-10T12:00:00Z",
               kind="issue", closed_at=""):
    """Monta um registro (issue, pull request ou commit) no formato do coletor."""
    return {
        "type": kind,
        "id": f"#{number}",
        "number": number,
        "title": title,
        "body": body,
        "author": author,
        "state": "" if kind == "commit" else ("closed" if closed_at else "open"),
        "labels": ["debt"],
        "created_at": created_at,
        "updated_at": created_at,
        "closed_at": closed_at,
        "url": f"https://github.com/acme/app/issues/{number}",
        "comments_count": len(comments),
        "comments": [
            {"author": comment_author, "body": comment_body,
             "created_at": created_at, "url": ""}
            for comment_author, comment_body in comments
        ],
        "comments_collected": True,
    }


SAMPLE_ISSUES = [
    make_issue(1, "Authentication needs refactoring",
               "Authentication needs refactoring and has no tests.\n\n"
               "```python\n# TODO: remove this hack\nlogin()\n```",
               comments=[("bob", "Agreed, this is great work so far."),
                         ("ci[bot]", "Coverage report: technical debt everywhere.")]),
    make_issue(2, "Upgrade the vulnerable dependency",
               "We use Python and Django. The vulnerable dependency must be upgraded.",
               created_at="2026-09-02T08:00:00Z"),
    make_issue(3, "Dark mode for the settings page",
               "It would be nice to have a dark mode.",
               created_at="2026-09-15T08:00:00Z"),
    make_issue(4, "Automated error report", "Stack trace attached.", author="telemetry[bot]"),
]


@pytest.fixture
def sample_collection():
    return {
        "metadata": {
            "source": "github", "owner": "acme", "repo": "app", "label": "debt",
            "requested": 4, "collected": 4, "collected_at": "2026-10-01T00:00:00+00:00",
            "comments_complete": True, "warning": "",
        },
        "issues": [dict(issue) for issue in SAMPLE_ISSUES],
    }


@pytest.fixture(scope="session")
def nlp():
    """Pipeline do spaCy; os testes que dependem dele são pulados sem o modelo."""
    from src.nlp_analyzer import load_pipeline
    try:
        return load_pipeline(config.DEFAULT_SPACY_MODEL)
    except OSError:
        pytest.skip(f"modelo {config.DEFAULT_SPACY_MODEL} não instalado")


@pytest.fixture
def data_dirs(tmp_path, monkeypatch):
    """Redireciona as pastas de dados para um diretório temporário."""
    for name in ("RAW_DIR", "PROCESSED_DIR", "RESULTS_DIR"):
        directory = tmp_path / name.lower()
        directory.mkdir()
        monkeypatch.setattr(config, name, directory)
    return tmp_path
