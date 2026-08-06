from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body
from inkletter.theme import Layout, Links, Text, Theme


def test_no_theme_means_the_default_theme():
    assert parse_markdown_to_mjml("Hello") == parse_markdown_to_mjml(
        "Hello", theme=Theme()
    )


def test_default_theme_emits_head():
    actual = parse_markdown_to_mjml("Hello", theme=Theme())
    print(actual)
    assert "<mj-head>" in actual
    assert "<mj-attributes>" in actual
    assert '<mj-style inline="inline">' in actual
    assert '<mj-body width="600px"' in actual


def test_custom_theme_values_reach_the_output():
    theme = Theme(
        layout=Layout(width="640px", background_color="#101010"),
        links=Links(color="#c0392b", underline=False),
    )
    actual = parse_markdown_to_mjml("A [link](https://x.com)", theme=theme)
    print(actual)
    assert '<mj-body width="640px" background-color="#101010">' in actual
    assert "a { color: #c0392b; text-decoration: none; }" in actual


def test_dark_preset():
    actual = parse_markdown_to_mjml("# Hello", theme=Theme.named("dark"))
    print(actual)
    # dark page, light text (values from the Slate palette)
    assert 'background-color="#0f172a"' in actual
    assert 'color="#e2e8f0"' in actual


def test_divider_carries_theme_attributes_inline():
    from inkletter.theme import Divider

    theme = Theme(divider=Divider(color="#123456", width="2px"))
    actual = parse_markdown_to_mjml("---", theme=theme)
    print(actual)
    body = actual[actual.find("<mj-body") :]
    assert body == """\
<mj-body width="600px" background-color="#f9fafb">
    <mj-section>
      <mj-column>
        <mj-divider border-color="#123456" border-width="2px"/>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""


def test_unthemed_divider_uses_the_default_theme():
    actual = parse_markdown_to_mjml("---")
    print(actual)
    expected = wrap_mjml_body('<mj-divider border-color="#e5e7eb" border-width="1px"/>')
    assert actual == expected


def test_theme_css_is_inlined_in_final_html():
    markdown = "# Big Title\n\nA [link](https://x.com) here."
    theme = Theme(links=Links(color="#c0392b"))
    html = parse_markdown_to_html(markdown, theme=theme)
    # mj-style inline="inline" must end up inlined into the tags
    assert "#c0392b" in html
    assert "font-size:28px" in html.replace(" ", "").replace('"', "")


def test_blockquote_is_semantic_html():
    actual = parse_markdown_to_mjml("> quoted", theme=Theme())
    assert "<blockquote>" in actual
    assert "font-style=" not in actual  # styling moved to mj-style


def test_table_theme_reaches_cells():
    from inkletter.theme import Table

    markdown = "| A |\n|---|\n| b |"
    theme = Theme(
        table=Table(border_color="#123456", header_background_color="#eeeeee")
    )
    actual = parse_markdown_to_mjml(markdown, theme=theme)
    print(actual)
    assert "border-bottom: 2px solid #123456" in actual  # header cell
    assert "background-color: #eeeeee" in actual
    assert "border-bottom: 1px solid #123456" in actual  # body cell


def test_table_typography_follows_the_theme():
    from inkletter.theme import Text

    theme = Theme(text=Text(color="#e2e8f0", font_family="Georgia, serif"))
    actual = parse_markdown_to_mjml("| A |\n|---|\n| b |", theme=theme)
    print(actual)
    # mj-table must not keep MJML's black/Ubuntu defaults
    assert '<mj-table color="#e2e8f0" font-family="Georgia, serif"' in actual


# --- Web fonts ---

LORA = "https://fonts.googleapis.com/css2?family=Lora"


def font_theme(**kwargs):
    return Theme(text=Text(font_family="Lora, Georgia, serif"), **kwargs)


def test_declared_font_is_emitted_in_the_head():
    actual = parse_markdown_to_mjml("Hello", theme=font_theme(fonts={"Lora": LORA}))
    print(actual)
    assert f'<mj-font name="Lora" href="{LORA}"/>' in actual


def test_fonts_are_emitted_in_their_declared_order():
    inter = "https://fonts.example/inter.css"
    theme = Theme(
        text=Text(font_family="Lora, Inter, serif"),
        fonts={"Lora": LORA, "Inter": inter},
    )
    actual = parse_markdown_to_mjml("Hello", theme=theme)
    print(actual)
    assert actual.index('name="Lora"') < actual.index('name="Inter"')


def test_no_fonts_leaves_the_head_untouched():
    # the feature costs nothing to whoever does not use it
    assert parse_markdown_to_mjml(
        "Hello", theme=font_theme()
    ) == parse_markdown_to_mjml(
        "Hello", theme=Theme(text=Text(font_family="Lora, Georgia, serif"))
    )
    assert "<mj-font" not in parse_markdown_to_mjml("Hello")


def test_declared_font_reaches_the_final_html():
    # the end-to-end proof of the mj-font contract: the compiler only
    # emits the font because text.font_family uses it
    html = parse_markdown_to_html(
        "# Title\n\nSome text.", theme=font_theme(fonts={"Lora": LORA})
    )
    assert "family=Lora" in html
    assert "[if !mso]" in html[: html.index("family=Lora")]  # MJML guards it


def test_an_email_without_fonts_makes_no_external_request():
    html = parse_markdown_to_html("# Title\n\nSome text.")
    assert "fonts.googleapis" not in html
