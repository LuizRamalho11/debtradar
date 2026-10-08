"""Coletor: normalização, paginação e tratamento de erros, sem acessar a rede."""
import json
import time

import pytest
import requests

from src.github_collector import (GitHubCollector, GitHubError, RateLimitError, mask_emails,
                                  normalize_comment, normalize_commit, normalize_issue,
                                  save_collection)


def fake_response(status=200, data=None, headers=None, next_url=None):
    """Monta uma resposta HTTP como a da API do GitHub."""
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(data if data is not None else []).encode()
    response.headers.update(headers or {"X-RateLimit-Remaining": "50"})
    if next_url:
        response.headers["Link"] = f'<{next_url}>; rel="next"'
    return response


class FakeSession:
    """Substitui requests.Session: devolve as respostas na ordem dada."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requested = []
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.requested.append(url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def collector_with(responses, token=""):
    collector = GitHubCollector(token)
    collector.session = FakeSession(responses)
    return collector


def api_issue(number, comments=0, pull_request=False):
    issue = {"number": number, "title": f"Issue {number}", "body": "Body",
             "user": {"login": "alice"}, "state": "open", "labels": [{"name": "debt"}],
             "created_at": "2026-08-01T00:00:00Z", "updated_at": "2026-08-02T00:00:00Z",
             "closed_at": None, "html_url": f"https://github.com/a/b/issues/{number}",
             "comments": comments}
    if pull_request:
        issue["pull_request"] = {}
    return issue


PAGE_2 = "https://api.github.com/repositories/1/issues?page=2"
LIMIT_HEADERS = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(time.time()) + 600)}


def test_normalize_issue_with_missing_fields():
    issue = normalize_issue({"number": 1, "title": None, "body": None, "user": None,
                             "labels": ["bug", {"name": "debt"}, {}]})
    assert issue["title"] == "" and issue["body"] == "" and issue["author"] == ""
    assert issue["labels"] == ["bug", "debt"]
    assert issue["closed_at"] == "" and issue["comments"] == []


def test_pagination_follows_link_header_and_skips_pull_requests():
    collector = collector_with([
        fake_response(data=[api_issue(1), api_issue(2, pull_request=True)], next_url=PAGE_2),
        fake_response(data=[api_issue(3), api_issue(4)]),
    ])
    collection = collector.collect("a", "b", limit=3)
    assert [issue["number"] for issue in collection["issues"]] == [1, 3, 4]
    assert collector.session.requested[1] == PAGE_2
    assert collection["metadata"]["collected"] == 3


def api_commit(sha, message, login="alice", parents=1):
    return {"sha": sha, "html_url": f"https://github.com/a/b/commit/{sha}",
            "author": {"login": login} if login else None, "parents": [{}] * parents,
            "commit": {"message": message, "author": {"name": "Alice A.", "date": "2026-08-05T10:00:00Z"}}}


def test_normalize_commit_splits_title_and_body():
    commit = normalize_commit(api_commit("abcdef1234", "Refactor parser\n\nRemove the hack.", login=None))
    assert (commit["type"], commit["id"], commit["number"]) == ("commit", "abcdef1", None)
    assert (commit["title"], commit["body"]) == ("Refactor parser", "Remove the hack.")
    assert commit["author"] == "Alice A."      # sem conta do GitHub, usa o nome do commit
    assert commit["state"] == "" and commit["comments"] == [] and commit["comments_collected"]
    assert commit["created_at"] == "2026-08-05T10:00:00Z"


def test_emails_are_masked_when_collecting():
    # Os dados coletados são publicados; e-mails de terceiros não devem ir junto.
    assert mask_emails("Ask ana.silva+dev@example.org or bob@mail.co.uk.") == (
        "Ask redacted@example.com or redacted@example.com.")
    # Não são e-mails: endereço de repositório, versão de pacote, decorador, pacote com escopo.
    for text in ("git@github.com:org/repo.git", "react@18.2.0", "@app.route", "@types/node"):
        assert mask_emails(text) == text
    issue = normalize_issue({"number": 1, "title": "Mail a@b.com", "body": "From c@d.io"})
    assert (issue["title"], issue["body"]) == ("Mail redacted@example.com", "From redacted@example.com")
    commit = normalize_commit(api_commit("abc1234", "Fix\n\nSigned-off-by: Ana <ana@corp.com>"))
    assert commit["body"] == "Signed-off-by: Ana <redacted@example.com>"
    assert normalize_comment({"body": "ping x@y.dev"})["body"] == "ping redacted@example.com"


def test_issues_carry_their_type():
    assert normalize_issue(api_issue(1))["type"] == "issue"
    pull_request = normalize_issue(api_issue(2, pull_request=True))
    assert (pull_request["type"], pull_request["id"]) == ("pull_request", "#2")


def test_collect_pull_requests_only():
    collector = collector_with([fake_response(data=[api_issue(1), api_issue(2, pull_request=True),
                                                    api_issue(3, pull_request=True)])])
    collection = collector.collect("a", "b", limit=5, sources=("prs",))
    assert [(r["type"], r["number"]) for r in collection["issues"]] == [("pull_request", 2), ("pull_request", 3)]
    assert collection["metadata"]["sources"] == ["prs"]


def test_collect_all_sources_in_one_pass_over_the_issue_list():
    collector = collector_with([
        fake_response(data=[api_issue(1), api_issue(2, pull_request=True), api_issue(3),
                            api_issue(4, pull_request=True), api_issue(5)]),
        fake_response(data=[api_commit("aaa1111", "Merge pull request #2", parents=2),
                            api_commit("bbb2222", "Fix typo"), api_commit("ccc3333", "Add tests"),
                            api_commit("ddd4444", "Not needed")]),
    ])
    collection = collector.collect("a", "b", limit=2, sources=("commits", "issues", "prs"))
    # Até 2 de cada fonte; o commit de merge é descartado.
    assert [r["id"] for r in collection["issues"]] == ["#1", "#3", "#2", "#4", "bbb2222", "ccc3333"]
    assert collection["metadata"]["sources"] == ["issues", "prs", "commits"]
    assert collection["metadata"]["collected"] == 6
    assert len(collector.session.requested) == 2
    assert collector.session.requested[1].endswith("/repos/a/b/commits")


def test_stops_requesting_pages_when_limit_is_reached():
    collector = collector_with([fake_response(data=[api_issue(1), api_issue(2)], next_url=PAGE_2)])
    assert len(collector.collect("a", "b", limit=2)["issues"]) == 2
    assert len(collector.session.requested) == 1


def test_comments_are_collected():
    comment = {"user": {"login": "bob"}, "body": "Nice", "created_at": "2026-08-03T00:00:00Z", "html_url": "u"}
    collector = collector_with([fake_response(data=[api_issue(1, comments=1)]), fake_response(data=[comment])])
    issue = collector.collect("a", "b", limit=1)["issues"][0]
    assert issue["comments"] == [{"author": "bob", "body": "Nice", "created_at": "2026-08-03T00:00:00Z", "url": "u"}]
    assert issue["comments_collected"] is True


def test_rate_limit_during_comments_keeps_the_issues():
    collector = collector_with([
        fake_response(data=[api_issue(1, comments=2), api_issue(2)]),
        fake_response(status=403, headers=LIMIT_HEADERS),
    ])
    collection = collector.collect("a", "b", limit=2)
    assert len(collection["issues"]) == 2
    assert collection["metadata"]["comments_complete"] is False
    assert "Limite de requisições" in collection["metadata"]["warning"]


def test_rate_limit_on_the_listing_is_an_error():
    with pytest.raises(RateLimitError, match="GITHUB_TOKEN"):
        collector_with([fake_response(status=403, headers=LIMIT_HEADERS)]).collect("a", "b", 5)


@pytest.mark.parametrize("status, message", [
    (401, "inválido ou expirado"),
    (404, "não encontrado"),
    (410, "desativadas"),
    (500, "erro HTTP 500"),
])
def test_http_errors_have_clear_messages(status, message):
    with pytest.raises(GitHubError, match=message):
        collector_with([fake_response(status=status)]).collect("a", "b", 5)


def test_timeout_and_connection_errors():
    with pytest.raises(GitHubError, match="não respondeu"):
        collector_with([requests.Timeout()]).collect("a", "b", 5)
    with pytest.raises(GitHubError, match="Falha de conexão"):
        collector_with([requests.ConnectionError("offline")]).collect("a", "b", 5)


def test_next_page_outside_the_api_is_not_followed():
    # O token vai no cabeçalho: o coletor não pode segui-lo para outro servidor.
    collector = collector_with([
        fake_response(data=[api_issue(1)], next_url="https://outro-servidor.example/page2")], token="abc")
    with pytest.raises(GitHubError, match="fora do GitHub"):
        collector.collect("a", "b", limit=5)
    assert len(collector.session.requested) == 1


def test_unexpected_payload():
    with pytest.raises(GitHubError, match="era esperada uma lista"):
        collector_with([fake_response(data={"message": "?"})]).collect("a", "b", 5)


def test_token_goes_in_the_header_only_when_present():
    assert "Authorization" not in GitHubCollector().session.headers
    assert GitHubCollector("abc").session.headers["Authorization"] == "Bearer abc"


def test_save_collection_names_the_file_and_backs_up_the_previous(tmp_path):
    collection = {"metadata": {"owner": "Acme", "repo": "App", "label": "kind/cleanup"}, "issues": []}
    path = save_collection(collection, tmp_path)
    assert path.name == "acme_app_kind-cleanup_issues.json"
    save_collection(collection, tmp_path)
    assert path.exists()
    assert len(list((tmp_path / "backup").glob("acme_app_kind-cleanup_issues_*.json"))) == 1


def test_file_name_carries_the_source(tmp_path):
    def name(sources):
        metadata = {"owner": "acme", "repo": "app", "label": "", "sources": sources}
        return save_collection({"metadata": metadata, "issues": []}, tmp_path).name
    assert name(["prs"]) == "acme_app_prs.json"
    assert name(["commits"]) == "acme_app_commits.json"
    assert name(["issues", "prs", "commits"]) == "acme_app_all.json"
