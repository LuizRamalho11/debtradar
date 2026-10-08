"""Pré-processamento: o que é removido, separado e preservado."""
from src.text_preprocessor import clean_text, is_bot, preprocess_issue
from tests.conftest import make_issue


def test_code_block_goes_to_code_field():
    text, code = clean_text("Before\n```py\nx = 1  # TODO\n```\nAfter")
    assert text == "Before\n\nAfter"
    assert code == "x = 1  # TODO"


def test_fence_with_four_backticks_leaves_no_backtick():
    # Defeito real: cercas ```` deixavam uma crase solta no texto.
    text, code = clean_text("a\n````\nlog line\n````\nb")
    assert "`" not in text
    assert code == "log line"


def test_unclosed_code_block_goes_to_the_end():
    text, code = clean_text("a\n```\nnever closed")
    assert text == "a"
    assert code == "never closed"


def test_inline_code_keeps_content_without_backticks():
    assert clean_text("call `run()` and ``@user``")[0] == "call run() and"


def test_links_images_and_urls():
    text, _ = clean_text("See [the docs](https://x.y/z) ![shot](https://x.y/a.png) https://x.y/b now")
    assert text == "See the docs now"


def test_link_text_with_brackets():
    # Defeito real: "[content[].text](url)" deixava "[...]( )" no texto.
    assert clean_text("[uses content[].text here](https://x.y)")[0] == "uses content[].text here"


def test_markdown_markers_are_removed():
    text, _ = clean_text("## Title\n\n- **bold** item\n- [x] done\n> quote\n\n| a | b |\n|---|---|\n| c | d |")
    assert text == "Title\n\nbold item\ndone\nquote\n\na b\nc d"


def test_html_tags_removed_but_placeholders_kept():
    text, _ = clean_text("<details><summary>Log</summary>path ~/.<app>/<name></details><!-- hidden -->")
    assert text == "Log path ~/.<app>/<name>"


def test_relevant_content_is_preserved():
    text, _ = clean_text("Fixes #123 in snake_case_name, keeps TODO and @types/node, drops @someone")
    assert text == "Fixes #123 in snake_case_name, keeps TODO and @types/node, drops"


def test_git_trailers_are_removed():
    # Defeito real: 206 linhas "Co-authored-by: Copilot" em 100 commits do VS Code
    # faziam "Copilot" aparecer 279 vezes entre as tecnologias.
    message = ("Fix the parser.\n\nCo-authored-by: Copilot <123+Copilot@users.noreply.github.com>\n"
               "Signed-off-by: Ana <ana@example.com>")
    assert clean_text(message)[0] == "Fix the parser."
    assert clean_text("Reviewed by: the team. Stand-by: mode")[0] == "Reviewed by: the team. Stand-by: mode"


def test_none_and_empty_input():
    assert clean_text(None) == ("", "")
    assert clean_text("") == ("", "")


def test_is_bot():
    assert is_bot("dependabot[bot]")
    assert is_bot("k8s-ci-robot")
    assert not is_bot("alice")


def test_preprocess_issue_joins_text_and_skips_bot_comments():
    issue = make_issue(7, "Title", "Body text.",
                       comments=[("bob", "Human comment."), ("ci[bot]", "Bot comment.")])
    document = preprocess_issue(issue)
    assert document["text"] == "Title\n\nBody text.\n\nHuman comment."
    assert document["bot_comments_ignored"] == 1
    assert document["number"] == 7
