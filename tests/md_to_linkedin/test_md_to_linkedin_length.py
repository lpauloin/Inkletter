import unicodedata

import pytest

from inkletter.counting import utf16_length
from inkletter.exceptions import LengthError
from inkletter.md_to_linkedin import parse_markdown_to_linkedin
from inkletter.shortener import URLFactory

# The platform counts UTF-16 code units — measured against its own refusal,
# which reports the length it computed. The count is declared fragment by
# fragment as the document is written, never taken over the finished
# string: only the render knows that a marker weighs a name, and that a
# long address will be a short link by the time it is read.


class Shortener(URLFactory):
    """A shortener that has not shortened anything yet, and says how wide
    its links are — which is the whole point: an author is counted for
    what will be published, before it exists."""

    link_length = 23


def test_plain_text_costs_its_characters(measured):
    assert measured("Bonjour") == 7


def test_an_accent_costs_one(measured):
    assert measured("étude") == 5


def test_a_decomposed_accent_is_composed_and_costs_one(measured):
    # measured: the platform counts e + combining acute as two units, and
    # shows one letter — so the letter goes out composed and costs one
    decomposed = unicodedata.normalize("NFD", "étude")
    assert len(decomposed) == 6
    assert parse_markdown_to_linkedin(decomposed) == "étude"
    assert measured(decomposed) == 5


def test_an_emoji_costs_two(measured):
    assert measured("Bonjour 👋") == 10


def test_a_line_break_costs_one(measured):
    assert measured("a\n\nb") == len("a\n\nb")


def test_markdown_marks_cost_nothing_since_nothing_renders_them(measured):
    assert measured("Du **gras**.") == len("Du gras.")


def test_a_unicode_substitute_costs_two_per_letter(measured):
    # four letters, eight units: the price of a look-alike
    assert measured("**gras**", unicode_styling=True) == 8


def test_a_mention_costs_the_name_it_displays(measured):
    assert measured("Merci [Acme](urn:li:organization:12345678) !") == len("Merci Acme !")


def test_a_degraded_mention_costs_what_it_shows(measured):
    # nothing to price apart: the arobase is text like any other now
    assert measured("[A|B](urn:li:organization:1)") == len("@A|B")


# --- A link costs what it will become ---
#
# The short link does not exist yet when the text is counted, and its
# width is fixed per organization — so the factory that will produce it
# is what declares that width.


def test_without_a_declared_width_a_link_costs_its_address(measured):
    actual = measured("[là](https://exemple.fr/une/adresse/longue)")
    assert actual == len("là : https://exemple.fr/une/adresse/longue")


def test_a_factory_that_says_its_width_prices_every_link_at_it(measured):
    actual = measured("[là](https://exemple.fr/une/adresse/longue)", url_factory=Shortener())
    assert actual == len("là : ") + 23


def test_a_bare_address_is_charged_once(measured):
    actual = measured("Voir https://exemple.fr/longue/adresse", url_factory=Shortener())
    assert actual == len("Voir ") + 23


def test_a_call_to_action_is_charged_like_any_link(measured):
    actual = measured(
        "**[Réserver](https://exemple.fr/une/adresse/longue)**", url_factory=Shortener()
    )
    assert actual == len("Réserver : ") + 23


# --- A price survives being laid out ---
#
# A label, a table cell, a quote: each is gathered before it is written
# back. What is priced inside it travels with it, or a mention would cost
# its marker again as soon as it appeared in a cell.


def test_a_mention_in_a_heading_still_costs_its_name(measured):
    assert measured("# Merci [Acme](urn:li:organization:12345678)") == len("Merci Acme")


def test_a_mention_in_a_table_cell_still_costs_its_name(measured):
    actual = measured("| [Acme](urn:li:organization:12345678) | b |\n|---|---|\n| 1 | 2 |")
    assert actual == len("Acme — b\n1 — 2")


def test_a_link_in_a_table_cell_still_costs_a_short_link(measured):
    actual = measured(
        "| a | [là](https://exemple.fr/tres/longue/adresse) |\n|---|---|", url_factory=Shortener()
    )
    assert actual == len("a — là : ") + 23


def test_a_link_in_a_quote_still_costs_a_short_link(measured):
    actual = measured(
        "> Voir [là](https://exemple.fr/tres/longue/adresse)", url_factory=Shortener()
    )
    assert actual == len("> Voir là : ") + 23


def test_a_mention_inside_bold_costs_its_name_and_the_substitutes(measured):
    actual = measured("**Merci [Acme](urn:li:organization:12345678)**", unicode_styling=True)
    assert actual == len("Merci Acme") + len("Merci")


# --- The count is laid out like the text ---
#
# Prices are declared fragment by fragment, and text and count are read
# off the same lines. So on a document where nothing is priced apart, the
# two must agree exactly — indentation, blank lines and trimmed ends
# included.


def test_a_document_with_nothing_special_weighs_its_own_characters(measured):
    document = """\
# Un titre

Un paragraphe avec un emoji 👋, un accent é et du `code`.

- une puce
  - une imbriquée
- une autre

| a | b |
|---|---|
| 1 | 2 |

> Une citation.
"""
    assert measured(document) == utf16_length(parse_markdown_to_linkedin(document))


# --- The one refusal ---


def test_over_the_ceiling_the_post_refuses_to_leave():
    with pytest.raises(LengthError) as refusal:
        parse_markdown_to_linkedin("x" * 4001)
    print(refusal.value)
    assert refusal.value.length == 4001
    assert refusal.value.limit == 4000
    assert str(refusal.value) == "the post is 4001 characters long, 4000 allowed (1 over)"


def test_the_ceiling_is_the_caller_s_to_lower():
    # a product guardrail, or the ceiling of wherever this text is going
    with pytest.raises(LengthError):
        parse_markdown_to_linkedin("x" * 3001, max_length=3000)


def test_no_ceiling_at_all_hands_the_decision_back():
    assert len(parse_markdown_to_linkedin("x" * 5000, max_length=None)) == 5000


def test_nothing_is_ever_truncated():
    assert parse_markdown_to_linkedin("x" * 4000) == "x" * 4000
