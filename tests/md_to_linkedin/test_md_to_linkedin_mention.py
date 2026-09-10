from inkletter.md_to_linkedin import parse_markdown_to_linkedin
from inkletter.shortener import URLFactory

# A mention is a CommonMark link whose text is the displayed name and
# whose target is the entity's URN. Nothing is stripped from the name and
# nothing is added to it: the marker is punctuation of the publishing API,
# and `@[<urn>|<name>]` is the one form that resolves — measured on real
# posts, where LinkedIn's own read-back form `@[Name](urn)` goes inert.

ACME = "[Acme](urn:li:organization:12345678)"


def test_a_mention_goes_out_as_a_marker():
    actual = parse_markdown_to_linkedin(f"Merci à {ACME} !")
    print(actual)
    assert actual == "Merci à @[urn:li:organization:12345678|Acme] !"


def test_the_read_back_form_is_never_produced():
    # written into a post, @[Nom](urn) goes inert and makes the whole text
    # escape itself
    assert "](urn:" not in parse_markdown_to_linkedin(f"Merci à {ACME}")


def test_a_person_is_mentioned_the_same_way():
    actual = parse_markdown_to_linkedin("[Jean Dupont](urn:li:person:ABC123)")
    print(actual)
    assert actual == "@[urn:li:person:ABC123|Jean Dupont]"


def test_the_name_travels_verbatim():
    # the match is exact and case-sensitive: a name touched up after being
    # chosen stops mentioning anybody
    actual = parse_markdown_to_linkedin("[L'Œil & Cie (Paris)](urn:li:organization:1)")
    print(actual)
    assert "|L'Œil & Cie (Paris)]" in actual


# --- What cannot be expressed ---
#
# `|` and `]` delimit the marker and no escape is documented for them, so
# a name carrying either cannot travel as a mention: it goes out as text
# rather than as a marker cut in half. The editor refuses such names at
# selection; this is the net under it.


def test_a_name_with_a_pipe_degrades_to_plain_text():
    actual = parse_markdown_to_linkedin("[Acme | Digital](urn:li:organization:1)")
    print(actual)
    assert actual == "@Acme | Digital"


def test_a_name_with_a_bracket_degrades_too():
    actual = parse_markdown_to_linkedin(r"[Acme \] Co](urn:li:organization:1)")
    print(actual)
    assert actual == "@Acme ] Co"


# --- The URL factory never sees a mention ---


class Shortener(URLFactory):
    def rewrite_link(self, url, is_button=False, is_bold=False):
        return "https://exa.mp/r/abc123"


def test_a_shortener_cannot_replace_an_urn_with_a_dead_link():
    # dispatch is on the exact class name, so visit_Link never sees a
    # Mention — and the factory is asked nothing about it either
    actual = parse_markdown_to_linkedin(
        f"{ACME} et [le site](https://exemple.fr)", url_factory=Shortener()
    )
    print(actual)
    assert "urn:li:organization:12345678" in actual
    assert "le site : https://exa.mp/r/abc123" in actual
