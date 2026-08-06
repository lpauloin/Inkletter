import re

import inkletter


def test_public_api_is_importable_from_the_package_root():
    mjml = inkletter.parse_markdown_to_mjml("Hello", theme=inkletter.Theme())
    assert mjml.startswith("<mjml>")

    html = inkletter.parse_markdown_to_html("Hello")
    assert "Hello" in html

    assert "dark" in inkletter.THEMES
    assert inkletter.URLFactory().rewrite_link("https://x.com") == "https://x.com"


def test_version_is_exposed():
    assert re.fullmatch(r"\d+\.\d+\.\d+", inkletter.__version__)
