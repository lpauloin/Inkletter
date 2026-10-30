import pytest

from inkletter import URLFactory
from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment


def test_emphasis_strong_and_strikethrough():
    actual = parse_markdown_to_html_fragment("Some *emphasis*, some **strong**, some ~~struck~~.")
    print(actual)
    assert (
        actual == "<p>Some <em>emphasis</em>, some <strong>strong</strong>, some <s>struck</s>.</p>"
    )


def test_code_span_is_escaped():
    actual = parse_markdown_to_html_fragment("Type `a < b` to compare.")
    print(actual)
    assert actual == "<p>Type <code>a &lt; b</code> to compare.</p>"


def test_link():
    actual = parse_markdown_to_html_fragment("Visit [our site](https://example.com).")
    print(actual)
    assert actual == '<p>Visit <a href="https://example.com">our site</a>.</p>'


def test_autolink():
    actual = parse_markdown_to_html_fragment("Visit <https://example.com> now!")
    print(actual)
    assert actual == '<p>Visit <a href="https://example.com">https://example.com</a> now!</p>'


def test_link_title_is_ignored():
    actual = parse_markdown_to_html_fragment('[site](https://example.com "A tooltip")')
    print(actual)
    assert actual == '<p><a href="https://example.com">site</a></p>'


def test_formatted_link_label_keeps_its_style():
    actual = parse_markdown_to_html_fragment("[the *full* guide](https://example.com)")
    print(actual)
    assert actual == '<p><a href="https://example.com">the <em>full</em> guide</a></p>'


def test_an_address_is_escaped_in_its_attribute():
    actual = parse_markdown_to_html_fragment("[guide](https://exemple.fr/?a=1&b=2)")
    print(actual)
    assert actual == '<p><a href="https://exemple.fr/?a=1&amp;b=2">guide</a></p>'


def test_a_link_to_another_scheme_is_its_label():
    actual = parse_markdown_to_html_fragment(
        "[click](javascript:alert(1)) and [data](data:text/html,x)"
    )
    print(actual)
    assert actual == "<p>click and data</p>"


def test_inline_html_tags_vanish():
    actual = parse_markdown_to_html_fragment("A <span>word</span> that matters<br>and the rest")
    print(actual)
    assert actual == "<p>A word that mattersand the rest</p>"


# --- Hashtags: text, as written ---


def test_a_hashtag_is_written_as_it_was():
    actual = parse_markdown_to_html_fragment("Nos #chiffres et #équipe_rh.")
    print(actual)
    assert actual == "<p>Nos #chiffres et #équipe_rh.</p>"


def test_a_heading_stays_a_heading():
    actual = parse_markdown_to_html_fragment("# Titre #tag")
    print(actual)
    assert actual == "<h1>Titre #tag</h1>"


# --- A bare address is a link ---


def test_a_bare_address_is_a_link():
    actual = parse_markdown_to_html_fragment("Voir https://exemple.fr/page.")
    print(actual)
    assert actual == '<p>Voir <a href="https://exemple.fr/page">https://exemple.fr/page</a>.</p>'


def test_a_bare_address_reaches_the_url_factory():
    class Short(URLFactory):
        def rewrite_link(self, url, is_button=False, is_bold=False):
            return "https://s.fr/x"

    actual = parse_markdown_to_html_fragment("Voir https://exemple.fr/page.", url_factory=Short())
    print(actual)
    assert actual == '<p>Voir <a href="https://s.fr/x">https://exemple.fr/page</a>.</p>'


def test_a_domain_without_its_scheme_links_to_it_and_keeps_its_label():
    actual = parse_markdown_to_html_fragment("Voir exemple.com/page.")
    print(actual)
    assert actual == '<p>Voir <a href="https://exemple.com/page">exemple.com/page</a>.</p>'


def test_what_only_looks_like_a_domain_is_text():
    actual = parse_markdown_to_html_fragment("Voir readme.md, a@exemple.com.")
    print(actual)
    assert actual == "<p>Voir readme.md, a@exemple.com.</p>"


# --- An address and a number ---


def test_a_mail_link():
    actual = parse_markdown_to_html_fragment("[Écrivez-nous](mailto:bonjour@exemple.fr)")
    print(actual)
    assert actual == '<p><a href="mailto:bonjour@exemple.fr">Écrivez-nous</a></p>'


def test_a_bare_address_between_brackets():
    actual = parse_markdown_to_html_fragment("Contact : <bonjour@exemple.fr>")
    print(actual)
    assert actual == '<p>Contact : <a href="mailto:bonjour@exemple.fr">bonjour@exemple.fr</a></p>'


def test_a_tel_link():
    actual = parse_markdown_to_html_fragment("[Appelez](tel:+331)")
    print(actual)
    assert actual == '<p><a href="tel:+331">Appelez</a></p>'


# --- A mention is the name it shows ---


def test_a_mention_is_its_name_never_its_urn():
    actual = parse_markdown_to_html_fragment("Bravo [Kehaia](urn:li:organization:123) !")
    print(actual)
    assert actual == "<p>Bravo Kehaia !</p>"


# --- Addresses meant to run something, and labels meant to open a tag ---


@pytest.mark.parametrize(
    "target",
    [
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        "vbscript:msgbox(1)",
        "data:text/html;base64,PHNjcmlwdD4=",
        "file:///etc/passwd",
        "&#106;avascript:alert(1)",
    ],
)
def test_a_link_to_a_scheme_that_runs_something_is_its_label(target):
    actual = parse_markdown_to_html_fragment(f"[click]({target})")
    print(actual)
    assert actual == "<p>click</p>"


def test_a_scheme_spelled_with_a_percent_is_no_scheme():
    # a browser reads `java%73cript:` as a relative path, never as a script
    actual = parse_markdown_to_html_fragment("[click](java%73cript:alert(1))")
    print(actual)
    assert actual == '<p><a href="java%73cript:alert(1)">click</a></p>'


@pytest.mark.parametrize("target", ["javascript:alert(1)", "data:text/html,x"])
def test_an_autolink_to_a_scheme_that_runs_something_is_text(target):
    actual = parse_markdown_to_html_fragment(f"<{target}>")
    print(actual)
    assert "<a " not in actual


@pytest.mark.parametrize(
    "target",
    [
        "https://exemple.fr",
        "http://exemple.fr",
        "/relative/path",
        "#section",
        "mailto:a@exemple.fr",
        "tel:+33100",
    ],
)
def test_the_schemes_that_link(target):
    actual = parse_markdown_to_html_fragment(f"[go]({target})")
    print(actual)
    assert actual.startswith("<p><a href=")


def test_an_address_cannot_break_out_of_its_attribute():
    actual = parse_markdown_to_html_fragment('[x](https://exemple.fr/"><script>alert(1)</script>)')
    print(actual)
    assert (
        actual
        == '<p><a href="https://exemple.fr/%22%3E%3Cscript%3Ealert(1)%3C/script%3E">x</a></p>'
    )


def test_an_address_with_parentheses():
    actual = parse_markdown_to_html_fragment("[wiki](https://fr.wikipedia.org/wiki/Paris_(France))")
    print(actual)
    assert actual == '<p><a href="https://fr.wikipedia.org/wiki/Paris_(France)">wiki</a></p>'


def test_a_link_with_an_empty_label_shows_its_address():
    actual = parse_markdown_to_html_fragment("[](https://exemple.fr)")
    print(actual)
    assert actual == '<p><a href="https://exemple.fr">https://exemple.fr</a></p>'


def test_a_link_with_a_blank_label_shows_its_address():
    actual = parse_markdown_to_html_fragment("[ ](https://exemple.fr)")
    print(actual)
    assert actual == '<p><a href="https://exemple.fr">https://exemple.fr</a></p>'


def test_angle_brackets_written_as_text_are_escaped():
    actual = parse_markdown_to_html_fragment("a \\<b\\> c and 3 < 4")
    print(actual)
    assert actual == "<p>a &lt;b&gt; c and 3 &lt; 4</p>"


def test_a_label_cannot_open_a_tag():
    actual = parse_markdown_to_html_fragment("[\\<b\\>bold\\</b\\>](https://exemple.fr)")
    print(actual)
    assert "<b>" not in actual
    assert "&lt;b&gt;" in actual


# --- Marks that do not close, or style nothing ---
