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
    expected = wrap_mjml_body(expected_content)
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
