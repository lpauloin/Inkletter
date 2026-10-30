import pytest

from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment


def test_paragraph():
    actual = parse_markdown_to_html_fragment("Hello everyone.")
    print(actual)
    assert actual == "<p>Hello everyone.</p>"


def test_paragraphs_are_two_paragraphs():
    actual = parse_markdown_to_html_fragment("First.\n\nSecond.")
    print(actual)
    assert actual == "<p>First.</p><p>Second.</p>"


def test_headings_keep_their_level():
    actual = parse_markdown_to_html_fragment("# One\n\n## Two\n\n### Three\n\n###### Six")
    print(actual)
    assert actual == "<h1>One</h1><h2>Two</h2><h3>Three</h3><h6>Six</h6>"


def test_setext_heading():
    actual = parse_markdown_to_html_fragment("Latest news\n-----------")
    print(actual)
    assert actual == "<h2>Latest news</h2>"


def test_blockquote():
    actual = parse_markdown_to_html_fragment("> a quote\n> on two lines")
    print(actual)
    assert actual == "<blockquote><p>a quote<br>on two lines</p></blockquote>"


def test_nested_blockquote():
    actual = parse_markdown_to_html_fragment("> level one\n> > level two")
    print(actual)
    assert (
        actual
        == "<blockquote><p>level one</p><blockquote><p>level two</p></blockquote></blockquote>"
    )


def test_block_code_is_preformatted_and_escaped():
    actual = parse_markdown_to_html_fragment('```\nprint("x" < 2)\n    indented\n```')
    print(actual)
    assert actual == '<pre><code>print("x" &lt; 2)\n    indented\n</code></pre>'


def test_thematic_break():
    actual = parse_markdown_to_html_fragment("before\n\n---\n\nafter")
    print(actual)
    assert actual == "<p>before</p><hr><p>after</p>"


def test_soft_break_is_a_line_break():
    actual = parse_markdown_to_html_fragment("line one\nline two")
    print(actual)
    assert actual == "<p>line one<br>line two</p>"


def test_hard_break_is_a_line_break():
    actual = parse_markdown_to_html_fragment("line one  \nline two")
    print(actual)
    assert actual == "<p>line one<br>line two</p>"


def test_empty_document():
    assert parse_markdown_to_html_fragment("") == ""
    assert parse_markdown_to_html_fragment("  \n \n") == ""


def test_crlf_input():
    actual = parse_markdown_to_html_fragment("line one\r\nline two\r\n\r\nnext")
    print(actual)
    assert actual == "<p>line one<br>line two</p><p>next</p>"


def test_text_is_escaped_non_ascii_untouched():
    actual = parse_markdown_to_html_fragment("Éléphant & Co, 2 < 3 > 1 — emoji 💌")
    print(actual)
    assert actual == "<p>Éléphant &amp; Co, 2 &lt; 3 &gt; 1 — emoji 💌</p>"


def test_entities_are_decoded_then_escaped():
    actual = parse_markdown_to_html_fragment("AT&amp;T and &copy; 2026")
    print(actual)
    assert actual == "<p>AT&amp;T and © 2026</p>"


def test_block_html_is_dropped():
    actual = parse_markdown_to_html_fragment("before\n\n<div onclick='x()'>a block</div>\n\nafter")
    print(actual)
    assert actual == "<p>before</p><p>after</p>"


def test_a_script_block_is_dropped():
    actual = parse_markdown_to_html_fragment("<script>alert(1)</script>\n\nafter")
    print(actual)
    assert actual == "<p>after</p>"


# --- Tags meant to escape the page, blocks inside blocks, and extreme inputs ---


@pytest.mark.parametrize(
    "markdown_text",
    [
        "<script>alert(1)</script>",
        "text <script>alert(1)</script> text",
        '<iframe src="https://evil.test"></iframe>',
        "<style>body{display:none}</style>",
        '<p onclick="alert(1)">x</p>',
        '<svg onload="alert(1)"></svg>',
        "<!-- a comment -->",
        "</p></body><body onload=alert(1)>",
    ],
)
def test_no_tag_of_the_author_reaches_the_fragment(markdown_text):
    actual = parse_markdown_to_html_fragment(markdown_text)
    print(actual)
    for tag in ("<script", "<iframe", "<style", "<svg", "onclick", "onload", "<!--", "<body"):
        assert tag not in actual


def test_a_heading_inside_a_quote():
    actual = parse_markdown_to_html_fragment("> ## Title\n> text")
    print(actual)
    assert actual == "<blockquote><h2>Title</h2><p>text</p></blockquote>"


@pytest.mark.parametrize("markdown_text", ["", " ", "\n", "\n\n\n", "\t", "  \n  \n"])
def test_blank_input_is_an_empty_fragment(markdown_text):
    assert parse_markdown_to_html_fragment(markdown_text) == ""


def test_many_blank_lines_between_paragraphs_are_one_break():
    actual = parse_markdown_to_html_fragment("one\n\n\n\n\ntwo")
    print(actual)
    assert actual == "<p>one</p><p>two</p>"


def test_trailing_spaces_and_tabs():
    actual = parse_markdown_to_html_fragment("text   \t")
    print(actual)
    assert actual == "<p>text</p>"


def test_a_long_document_renders_whole():
    words = " ".join(f"mot{index}" for index in range(5000))
    actual = parse_markdown_to_html_fragment(words)
    assert actual.startswith("<p>mot0 ") and actual.endswith(" mot4999</p>")


def test_a_null_and_control_characters():
    # CommonMark: a NUL is replaced, the other controls are text
    actual = parse_markdown_to_html_fragment("a\x00b\x07c")
    print(actual)
    assert actual == "<p>a\ufffdb\x07c</p>"


def test_rtl_and_combining_text_is_untouched():
    actual = parse_markdown_to_html_fragment("مرحبا — été — 👩‍👩‍👧")
    print(actual)
    assert actual == "<p>مرحبا — été — 👩‍👩‍👧</p>"
