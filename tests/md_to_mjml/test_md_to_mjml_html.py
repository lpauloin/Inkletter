from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body

# --- Block-level raw HTML ---


def test_block_html():
    markdown_input = "<div>hello</div>"
    expected_content = """\
<mj-raw>
  <div>hello</div>
</mj-raw>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_block_html_between_paragraphs():
    markdown_input = """\
Before.

<div>raw</div>

After."""
    expected_content = """\
<mj-text>
  Before.
</mj-text>
<mj-raw>
  <div>raw</div>
</mj-raw>
<mj-text>
  After.
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Inline raw HTML ---


def test_inline_html_in_paragraph():
    markdown_input = "Un <span>mot</span> important"
    expected_content = """<mj-text>
  Un <span>mot</span> important
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_inline_html_br():
    markdown_input = "ligne un<br>ligne deux"
    expected_content = """<mj-text>
  ligne un<br>ligne deux
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_inline_html_is_not_escaped_but_text_is():
    markdown_input = "A & B <b>bold</b>"
    expected_content = """<mj-text>
  A &amp; B <b>bold</b>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_inline_html_in_heading():
    markdown_input = "# Titre <em>mixte</em>"
    expected_content = """\
<mj-text>
  <h1>Titre <em>mixte</em></h1>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected
