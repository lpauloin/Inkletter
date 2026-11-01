from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body, wrap_mjml_document


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


def test_an_empty_lang_leaves_the_root_bare():
    actual = parse_markdown_to_mjml("Hello", lang="")
    print(actual)
    assert actual.startswith("<mjml>")


def test_lang_is_escaped():
    actual = parse_markdown_to_mjml("Hello", lang='en"><x')
    print(actual)
    assert actual.startswith('<mjml lang="en&quot;&gt;&lt;x">')


def test_a_wrapped_document_takes_its_lang():
    assert wrap_mjml_document("<mj-section></mj-section>", lang="de").startswith('<mjml lang="de">')
    assert wrap_mjml_body("<mj-text>Hallo</mj-text>", lang="de").startswith('<mjml lang="de">')


def test_a_wrapped_document_without_lang_is_unchanged():
    assert wrap_mjml_document("<mj-section></mj-section>").startswith("<mjml>")
