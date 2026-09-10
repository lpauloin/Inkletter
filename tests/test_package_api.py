import re

import pytest

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


def test_the_linkedin_output_and_its_refusal_are_public():
    # a caller catches the refusal by name, so the name has to be there
    with pytest.raises(inkletter.LengthError):
        inkletter.parse_markdown_to_linkedin("x" * 10, max_length=5)
    assert inkletter.parse_markdown_to_linkedin("**Salut**") == "Salut"
