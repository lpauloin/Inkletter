import pytest

from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.theme import Layout, Links, Theme


def test_no_theme_has_no_head():
    actual = parse_markdown_to_mjml("Hello")
    assert "<mj-head>" not in actual
    assert "<mj-body>" in actual


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


def test_night_preset():
    actual = parse_markdown_to_mjml("# Hello", theme=Theme.named("night"))
    print(actual)
    # dark page, light text (values from the Slate palette)
    assert 'background-color="#0f172a"' in actual
    assert 'color="#e2e8f0"' in actual


def test_themed_divider_relies_on_attributes():
    actual = parse_markdown_to_mjml("---", theme=Theme())
    assert "<mj-divider/>" in actual
    assert '<mj-divider border-color="#e5e7eb" border-width="1px"/>' in actual  # head


def test_unthemed_divider_keeps_legacy_attributes():
    actual = parse_markdown_to_mjml("---")
    assert '<mj-divider border-color="#cccccc" border-width="1px"/>' in actual


def test_use_style_is_a_deprecated_alias_of_default_theme():
    with pytest.deprecated_call():
        legacy = parse_markdown_to_mjml("Hello", use_style=True)
    assert legacy == parse_markdown_to_mjml("Hello", theme=Theme())


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
