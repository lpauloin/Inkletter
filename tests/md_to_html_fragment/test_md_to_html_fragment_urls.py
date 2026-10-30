from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment
from inkletter.shortener import URLFactory


class PrefixFactory(URLFactory):
    def rewrite_link(self, url, is_button=False, is_bold=False):
        return f"https://short.test/?u={url}"


def test_rewritten_links_reach_the_fragment():
    actual = parse_markdown_to_html_fragment(
        "Visit [the site](https://example.com).", url_factory=PrefixFactory()
    )
    print(actual)
    assert (
        actual == '<p>Visit <a href="https://short.test/?u=https://example.com">the site</a>.</p>'
    )


def test_rewritten_button_href_reaches_the_fragment():
    actual = parse_markdown_to_html_fragment(
        "**[Go](https://example.com/go)**", url_factory=PrefixFactory()
    )
    print(actual)
    assert (
        actual
        == '<p><a href="https://short.test/?u=https://example.com/go"><strong>Go</strong></a></p>'
    )


# --- A hand-written anchor is a link, its tag rebuilt from its address ---


def test_an_inline_anchor_is_a_link():
    actual = parse_markdown_to_html_fragment(
        'Cliquez <a href="https://app/account" onclick="x()">Ajuster</a> ici.'
    )
    print(actual)
    assert actual == '<p>Cliquez <a href="https://app/account">Ajuster</a> ici.</p>'


def test_it_reads_like_a_markdown_link():
    written_both_ways = (
        "Cliquez [Ajuster](https://app/account) ici.",
        'Cliquez <a href="https://app/account">Ajuster</a> ici.',
    )
    outputs = {parse_markdown_to_html_fragment(source) for source in written_both_ways}
    print(outputs)
    assert len(outputs) == 1


def test_single_quotes_and_extra_attributes_are_read_too():
    actual = parse_markdown_to_html_fragment(
        "Voir <a class='x' href='https://x.com/p'>la page</a>."
    )
    print(actual)
    assert actual == '<p>Voir <a href="https://x.com/p">la page</a>.</p>'


def test_two_anchors_keep_their_own_urls():
    actual = parse_markdown_to_html_fragment(
        '<a href="https://a.test">A</a> et <a href="https://b.test">B</a>'
    )
    print(actual)
    assert actual == '<p><a href="https://a.test">A</a> et <a href="https://b.test">B</a></p>'


def test_an_anchor_without_href_adds_nothing():
    actual = parse_markdown_to_html_fragment("Un <a name='ancre'>repère</a> ici.")
    print(actual)
    assert actual == "<p>Un repère ici.</p>"


def test_an_anchor_to_another_scheme_is_its_text():
    actual = parse_markdown_to_html_fragment('Un <a href="javascript:x()">piège</a> ici.')
    print(actual)
    assert actual == "<p>Un piège ici.</p>"


def test_an_anchor_to_another_scheme_inside_one_leaves_it_open():
    # its closing tag closes nothing it did not open
    actual = parse_markdown_to_html_fragment(
        '<a href="https://a.fr">x <a href="javascript:y">z</a> w</a>'
    )
    print(actual)
    assert actual == '<p><a href="https://a.fr">x z w</a></p>'


def test_an_anchor_never_closed_closes_with_its_block():
    actual = parse_markdown_to_html_fragment(
        'Ouverte <a href="https://a.test">jamais fermée\n\nSuite.'
    )
    print(actual)
    assert actual == '<p>Ouverte <a href="https://a.test">jamais fermée</a></p><p>Suite.</p>'


def test_other_inline_tags_still_vanish():
    actual = parse_markdown_to_html_fragment("Du <span>texte</span> et du <b>gras</b>.")
    print(actual)
    assert actual == "<p>Du texte et du gras.</p>"


def test_a_bare_address_is_read_before_the_marks_inside_it():
    # it never ends on a mark, which stays text after it
    actual = parse_markdown_to_html_fragment("Voir https://exemple.fr/*etoiles* merci")
    print(actual)
    assert actual == (
        '<p>Voir <a href="https://exemple.fr/*etoiles">https://exemple.fr/*etoiles</a>* merci</p>'
    )


def test_a_bare_address_inside_a_link_label_is_its_text():
    actual = parse_markdown_to_html_fragment("[voir https://a.fr ici](https://b.fr)")
    print(actual)
    assert actual == '<p><a href="https://b.fr">voir https://a.fr ici</a></p>'
