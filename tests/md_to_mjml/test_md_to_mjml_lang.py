from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml


def test_lang_goes_on_the_mjml_root():
    actual = parse_markdown_to_mjml("Hello", lang="en")
    print(actual)
    assert actual.startswith('<mjml lang="en">')


def test_no_lang_leaves_the_root_bare():
    actual = parse_markdown_to_mjml("Hello")
    print(actual)
    assert actual.startswith("<mjml>")


def test_lang_reaches_the_html():
    actual = parse_markdown_to_html("Hello", lang="fr")
    print(actual)
    assert '<html lang="fr"' in actual
    assert 'lang="und"' not in actual


def test_lang_is_escaped():
    actual = parse_markdown_to_mjml("Hello", lang='en"><x')
    print(actual)
    assert actual.startswith('<mjml lang="en&quot;&gt;&lt;x">')
