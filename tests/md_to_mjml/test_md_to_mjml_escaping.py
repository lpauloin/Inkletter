import re

import pytest

from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body

# --- Text content escaping ---


@pytest.mark.parametrize(
    "markdown_input, inner_html",
    [
        ("5 < 10 et A&B", "5 &lt; 10 et A&amp;B"),
        ("a > b", "a &gt; b"),
        ("Tom & Jerry", "Tom &amp; Jerry"),
    ],
)
def test_special_characters_in_text(markdown_input, inner_html):
    expected_content = f"""<mj-text>
  {inner_html}
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_special_characters_in_heading():
    markdown_input = "# Prix < 100 & offres"
    expected_content = """\
<mj-text>
  <h1>Prix &lt; 100 &amp; offres</h1>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    # the h1 is plain text, so it also becomes the document title
    expected = wrap_mjml_body(expected_content, title="Prix < 100 & offres")
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_special_characters_in_emphasis():
    markdown_input = "Text in *a < b* here"
    expected_content = """<mj-text>
  Text in <em>a &lt; b</em> here
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_special_characters_in_table_cell():
    markdown_input = "| A&B |\n|-----|\n| a<b |"
    actual = parse_markdown_to_mjml(markdown_input)
    print(actual)
    assert "A&amp;B" in actual
    assert "a&lt;b" in actual


# --- Attribute value escaping ---


def test_ampersand_in_link_href():
    markdown_input = "[link](https://example.com/?a=1&b=2)"
    expected_content = """<mj-text>
  <a href="https://example.com/?a=1&amp;b=2">link</a>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_quotes_in_link_title():
    markdown_input = '[x](https://example.com "It\'s \\"quoted\\"")'
    expected_content = """<mj-text>
  <a href="https://example.com" title="It&#x27;s &quot;quoted&quot;">x</a>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_special_characters_in_image_alt():
    markdown_input = '![Tom & "Jerry"](https://picsum.photos/600/300)'
    expected_content = """\
<mj-image src="https://picsum.photos/600/300" alt="Tom &amp; &quot;Jerry&quot;"/>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- HTML entities (CommonMark decodes them everywhere but in code) ---


def test_entities_are_decoded_in_text():
    actual = parse_markdown_to_mjml("AT&amp;T coûte 5&nbsp;€ et &copy; 2026")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  AT&amp;T coûte 5 € et © 2026
</mj-text>""")
    assert actual == expected


def test_numeric_entities_are_decoded():
    actual = parse_markdown_to_mjml("&#169; et &#x2764;")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  © et ❤
</mj-text>""")
    assert actual == expected


def test_double_entity_stays_literal():
    # the author wrote &amp;amp; to display "&amp;"
    actual = parse_markdown_to_mjml("&amp;amp;")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  &amp;amp;
</mj-text>""")
    assert actual == expected


def test_entities_stay_literal_in_code():
    actual = parse_markdown_to_mjml("Le code `&amp;` puis :\n\n```\n&copy;\n```")
    print(actual)
    assert "<code>&amp;amp;</code>" in actual  # renders the literal "&amp;"
    assert "&amp;copy;" in actual  # renders the literal "&copy;"


def test_entities_are_decoded_in_alt_and_title():
    actual = parse_markdown_to_mjml('![AT&amp;T](https://x.com/i.png "Tom &amp; Jerry")')
    print(actual)
    expected = wrap_mjml_body(
        '<mj-image src="https://x.com/i.png" alt="AT&amp;T" title="Tom &amp; Jerry"/>'
    )
    assert actual == expected


def test_entity_cannot_smuggle_html():
    # &lt;script&gt; decodes to <script> then gets re-escaped: no injection
    actual = parse_markdown_to_mjml("&lt;script&gt;alert(1)&lt;/script&gt;")
    print(actual)
    assert "<script>" not in actual
    assert "&lt;script&gt;" in actual


# --- Backslash escapes, the ones sample/DJANGO.md tells you to apply ---
#
# A value substituted into a Markdown document is Markdown. The guide
# hands out a filter that backslash-escapes ASCII punctuation, which is
# only worth anything if those escapes survive the conversion.

PUNCTUATION = re.compile(r"([!-/:-@\[-`{-~])")


def md_escape(value):
    """The escaping helper documented in sample/DJANGO.md."""
    return PUNCTUATION.sub(r"\\\1", value)


@pytest.mark.parametrize(
    "value",
    [
        "_Bob_",
        "**shouting**",
        "# not a heading",
        "- not a list item",
        "[click](https://evil.example)",
        "back\\slash",
    ],
)
def test_an_escaped_value_stays_literal(value):
    actual = parse_markdown_to_mjml(f"Value: {md_escape(value)}.")
    print(actual)
    assert f"Value: {value}." in actual
    assert "<em>" not in actual and "<strong>" not in actual


def test_an_escaped_value_cannot_inject_html():
    actual = parse_markdown_to_mjml(f"Value: {md_escape('<script>alert(1)</script>')}.")
    print(actual)
    assert "<script>" not in actual
    assert "alert(1)" in actual


def test_an_escaped_pipe_does_not_split_a_cell():
    # the reason the helper escapes punctuation Gruber never listed: the
    # pipe belongs to GFM tables, and a value holding one would otherwise
    # open a column of its own
    actual = parse_markdown_to_mjml(f"| A | B |\n|---|---|\n| {md_escape('one | two')} | ok |")
    print(actual)
    assert actual.count("<td") == 2
    assert "one | two" in actual
