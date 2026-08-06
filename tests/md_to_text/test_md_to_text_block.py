from inkletter.md_to_text import parse_markdown_to_text


def test_paragraph():
    actual = parse_markdown_to_text("Hello everyone.")
    print(actual)
    assert actual == "Hello everyone.\n"


def test_paragraphs_are_separated_by_a_blank_line():
    actual = parse_markdown_to_text("First.\n\nSecond.")
    print(actual)
    assert actual == "First.\n\nSecond.\n"


def test_h1_is_uppercased_and_underlined():
    actual = parse_markdown_to_text("# My newsletter")
    print(actual)
    assert actual == "MY NEWSLETTER\n=============\n"


def test_h2_is_underlined():
    actual = parse_markdown_to_text("## Latest news")
    print(actual)
    assert actual == "Latest news\n-----------\n"


def test_h3_is_a_bare_line():
    actual = parse_markdown_to_text("### Details\n\nsome text")
    print(actual)
    assert actual == "Details\n\nsome text\n"


def test_blockquote_is_prefixed():
    actual = parse_markdown_to_text("> a quote\n> on two lines")
    print(actual)
    assert actual == "> a quote\n> on two lines\n"


def test_nested_blockquote():
    actual = parse_markdown_to_text("> level one\n> > level two")
    print(actual)
    assert actual == "> level one\n>\n> > level two\n"


def test_block_code_is_indented():
    actual = parse_markdown_to_text('```\nprint("x")\n    indented\n```')
    print(actual)
    assert actual == '    print("x")\n        indented\n'


def test_thematic_break_is_a_dash_line():
    actual = parse_markdown_to_text("before\n\n---\n\nafter")
    print(actual)
    assert actual == "before\n\n" + "-" * 40 + "\n\nafter\n"


def test_soft_break_is_a_line_break():
    actual = parse_markdown_to_text("line one\nline two")
    print(actual)
    assert actual == "line one\nline two\n"


def test_hard_break_is_a_line_break():
    actual = parse_markdown_to_text("line one  \nline two")
    print(actual)
    assert actual == "line one\nline two\n"


def test_empty_document():
    assert parse_markdown_to_text("") == ""
    assert parse_markdown_to_text("  \n \n") == ""


def test_crlf_input():
    actual = parse_markdown_to_text("line one\r\nline two\r\n\r\nnext")
    print(actual)
    assert "\r" not in actual
    assert actual == "line one\nline two\n\nnext\n"


def test_non_ascii_is_untouched():
    # no HTML escaping in plain text: & and < stay as written
    actual = parse_markdown_to_text("Éléphant & Co, 2 < 3 — emoji 💌")
    print(actual)
    assert actual == "Éléphant & Co, 2 < 3 — emoji 💌\n"


def test_entities_are_decoded():
    actual = parse_markdown_to_text("AT&amp;T and &copy; 2026")
    print(actual)
    assert actual == "AT&T and © 2026\n"


def test_block_html_is_ignored():
    actual = parse_markdown_to_text("before\n\n<div>a block</div>\n\nafter")
    print(actual)
    assert actual == "before\n\nafter\n"
