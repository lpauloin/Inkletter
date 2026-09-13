import pytest

from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body

# --- Italic with * and _ ---


@pytest.mark.parametrize(
    "markdown_input, inner_html",
    [
        ("Text in *italic*", "Text in <em>italic</em>"),
        ("Text in _italic_", "Text in <em>italic</em>"),
    ],
)
def test_italic_variants(markdown_input, inner_html):
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


# --- Bold with ** and __ ---


@pytest.mark.parametrize(
    "markdown_input, inner_html",
    [
        ("Text in **bold**", "Text in <strong>bold</strong>"),
        ("Text in __bold__", "Text in <strong>bold</strong>"),
    ],
)
def test_bold_variants(markdown_input, inner_html):
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


# --- Strikethrough (~~text~~) ---


def test_strikethrough():
    markdown_input = """Text with ~~strikethrough~~ effect."""
    expected_content = """<mj-text>
  Text with <del>strikethrough</del> effect.
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Combined Bold + Italic (***text***) ---


def test_bold_and_italic_combined():
    markdown_input = """Text with ***bold and italic*** formatting."""
    expected_content = """<mj-text>
  Text with <em><strong>bold and italic</strong></em> formatting.
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Inline code span ---


def test_inline_code():
    markdown_input = """Use the `print()` function."""
    expected_content = """\
<mj-text>
  Use the <code>print()</code> function.
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_inline_code_with_html():
    markdown_input = """Use the `<pre>code</pre>` tags."""
    expected_content = """\
<mj-text>
  Use the <code>&lt;pre&gt;code&lt;/pre&gt;</code> tags.
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Inline link ---


def test_inline_link():
    markdown_input = """Visit [OpenAI](https://openai.com)."""
    expected_content = """<mj-text>
  Visit <a href="https://openai.com">OpenAI</a>.
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Hard line break ---


def test_inline_hard_linebreak():
    markdown_input = """Line one.  
Line two."""
    expected_content = """<mj-text>
  Line one.<br/>
  Line two.
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Soft break ---


def test_inline_softbreak():
    markdown_input = """Line one
Line two"""
    expected_content = """<mj-text>
  Line one<br/>
  Line two
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Link ---


def test_link():
    markdown_input = """[OpenAI](https://openai.com)"""
    expected_content = """<mj-text>
  <a href="https://openai.com">OpenAI</a>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Link containing Bold text ---


def test_link_with_bold_text():
    markdown_input = """[**Bold Link**](https://example.com)"""
    expected_content = """<mj-text>
  <a href="https://example.com"><strong>Bold Link</strong></a>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Link containing Italic text ---


def test_link_with_italic_text():
    markdown_input = """[*Italic Link*](https://example.com)"""
    expected_content = """<mj-text>
  <a href="https://example.com"><em>Italic Link</em></a>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Link containing Bold and Italic combined text ---


def test_link_with_bold_and_italic_text():
    markdown_input = """[***Bold and Italic Link***](https://example.com)"""
    expected_content = """<mj-text>
  <a href="https://example.com"><em><strong>Bold and Italic Link</strong></em></a>
</mj-text>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Hashtags ---


def test_a_hashtag_is_text_unless_the_theme_colours_it():
    actual = parse_markdown_to_mjml("Nos #chiffres et #équipe_rh.")
    assert wrap_mjml_body("<mj-text>\n  Nos #chiffres et #équipe_rh.\n</mj-text>") == actual


def test_a_themed_hashtag_is_set_apart_inline():
    from inkletter.theme import Hashtags, Theme

    theme = Theme(hashtags=Hashtags(color="#0a66c2"))
    actual = parse_markdown_to_mjml("Un **#tag**.", theme=theme)
    expected = wrap_mjml_body(
        '<mj-text>\n  Un <strong><span style="color: #0a66c2;">#tag</span></strong>.\n</mj-text>'
    )
    assert actual == expected


def test_a_hashtag_alone_still_opens_its_text_block():
    actual = parse_markdown_to_mjml("#tag")
    assert wrap_mjml_body("<mj-text>\n  #tag\n</mj-text>") == actual


# --- A bare address is a link ---


def test_a_bare_address_is_an_anchor():
    actual = parse_markdown_to_mjml("Voir https://exemple.fr/page.")
    expected = wrap_mjml_body(
        '<mj-text>\n  Voir <a href="https://exemple.fr/page">https://exemple.fr/page</a>.\n</mj-text>'
    )
    assert actual == expected


def test_a_bare_address_alone_in_bold_is_a_button():
    actual = parse_markdown_to_mjml("**https://exemple.fr**")
    assert '<mj-button href="https://exemple.fr"' in actual


# --- An address and a number are anchors a mail client can act on ---


def test_a_mail_link_is_an_anchor():
    actual = parse_markdown_to_mjml("[Écrivez-nous](mailto:bonjour@exemple.fr)")
    expected = wrap_mjml_body(
        '<mj-text>\n  <a href="mailto:bonjour@exemple.fr">Écrivez-nous</a>\n</mj-text>'
    )
    assert actual == expected


def test_a_lone_bold_mail_link_is_a_button():
    assert '<mj-button href="mailto:a@b.fr"' in parse_markdown_to_mjml(
        "**[Écrivez-nous](mailto:a@b.fr)**"
    )
