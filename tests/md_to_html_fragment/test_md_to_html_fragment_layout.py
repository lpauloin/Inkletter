from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment

URL = "https://example.com/go"


def test_a_button_is_a_bold_link():
    actual = parse_markdown_to_html_fragment(f"**[Get started]({URL})**")
    print(actual)
    assert actual == f'<p><a href="{URL}"><strong>Get started</strong></a></p>'


def test_button_disabled_renders_as_a_bold_link_too():
    actual = parse_markdown_to_html_fragment(f"**[Get started]({URL})**", bold_link_is_button=False)
    print(actual)
    assert actual == f'<p><strong><a href="{URL}">Get started</a></strong></p>'


def test_a_button_to_another_scheme_is_its_label():
    actual = parse_markdown_to_html_fragment("**[Get started](javascript:go())**")
    print(actual)
    assert "href" not in actual
    assert "Get started" in actual


def test_image_row_is_its_alts():
    actual = parse_markdown_to_html_fragment(
        "![Left view](https://x.com/a.png) ![Right view](https://x.com/b.png)"
    )
    print(actual)
    assert "img" not in actual
    assert "Left view" in actual and "Right view" in actual


def test_media_object_is_its_alt_then_text():
    actual = parse_markdown_to_html_fragment(
        "![Portrait](https://x.com/j.png) Jane joined the team."
    )
    print(actual)
    assert "img" not in actual
    assert actual.startswith("<p>Portrait")
    assert "Jane joined the team." in actual
