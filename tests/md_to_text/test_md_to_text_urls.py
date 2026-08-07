from inkletter.md_to_text import parse_markdown_to_text
from inkletter.shortener import URLFactory


class PrefixFactory(URLFactory):
    def rewrite_link(self, url):
        return f"https://short.test/?u={url}"


def test_rewritten_links_reach_the_text():
    actual = parse_markdown_to_text(
        "Visit [the site](https://example.com).", url_factory=PrefixFactory()
    )
    print(actual)
    assert actual == "Visit the site <https://short.test/?u=https://example.com>.\n"


def test_rewritten_button_href_reaches_the_text():
    # same pass-ordering invariant as SPEC-URLS: the Button inherits the
    # already rewritten Link href
    actual = parse_markdown_to_text("**[Go](https://example.com/go)**", url_factory=PrefixFactory())
    print(actual)
    assert actual == "→ Go : https://short.test/?u=https://example.com/go\n"


# --- A hand-written anchor keeps its URL ---
#
# The text half is the one meant to stay readable everywhere; dropping
# the URL there was a silent loss, and it made the two halves of the
# same multipart disagree.


def test_an_inline_anchor_spells_out_its_url():
    actual = parse_markdown_to_text('Cliquez <a href="https://app/account">Ajuster</a> ici.')
    print(actual)
    assert actual == "Cliquez Ajuster <https://app/account> ici.\n"


def test_it_reads_like_a_markdown_link():
    written_both_ways = (
        "Cliquez [Ajuster](https://app/account) ici.",
        'Cliquez <a href="https://app/account">Ajuster</a> ici.',
    )
    outputs = {parse_markdown_to_text(source) for source in written_both_ways}
    print(outputs)
    assert len(outputs) == 1


def test_single_quotes_and_extra_attributes_are_read_too():
    actual = parse_markdown_to_text("Voir <a class='x' href='https://x.com/p'>la page</a>.")
    print(actual)
    assert "<https://x.com/p>" in actual


def test_two_anchors_keep_their_own_urls():
    actual = parse_markdown_to_text(
        '<a href="https://a.test">A</a> et <a href="https://b.test">B</a>'
    )
    print(actual)
    assert "A <https://a.test>" in actual
    assert "B <https://b.test>" in actual


def test_an_anchor_without_href_adds_nothing():
    actual = parse_markdown_to_text("Un <a name='ancre'>repère</a> ici.")
    print(actual)
    assert actual == "Un repère ici.\n"


def test_other_inline_tags_still_vanish():
    actual = parse_markdown_to_text("Du <span>texte</span> et du <b>gras</b>.")
    print(actual)
    assert actual == "Du texte et du gras.\n"
