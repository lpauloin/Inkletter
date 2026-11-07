"""Mentions, strikethrough and lists of tasks, for a page or an editor that
wants them written its way — each asked for, none by default:

| Option            | What the fragment writes                                  |
|-------------------|-----------------------------------------------------------|
| `mentions`        | the attributes the caller gives for a mention's URN, or `@name`|
| `unicode_strike`  | strikethrough as its Unicode look-alike                   |
| `task_paragraphs` | a list holding tasks as a paragraph per item              |
"""

import pytest

from inkletter import parse_markdown_to_html_fragment


def entity_of(urn):
    """A caller's own rule: a company read back as an entity, anyone else
    left to `@name`."""
    kind, _, number = urn.removeprefix("urn:li:").partition(":")
    return (
        {"data-type": "mention", "data-entity-urn": f"company:{number}"}
        if kind == "organization" and number
        else None
    )


def public_page_of(urn):
    """Another caller's rule: a company's public page."""
    return {"href": f"https://exemple.fr/pages/{urn.rsplit(':', 1)[-1]}"}


def a_script(urn):
    return {"href": "javascript:alert(1)"}


def test_without_the_option_a_mention_is_its_name():
    actual = parse_markdown_to_html_fragment("Bravo [Acme](urn:li:organization:42) !")
    assert actual == "<p>Bravo Acme !</p>"


def test_a_mention_is_the_entity_the_caller_gives_for_its_urn():
    actual = parse_markdown_to_html_fragment(
        "Bravo [Acme](urn:li:organization:42) !", mentions=entity_of
    )
    print(actual)
    assert actual == '<p>Bravo <a data-type="mention" data-entity-urn="company:42">Acme</a> !</p>'


def test_a_mention_may_be_a_link_to_a_public_page():
    actual = parse_markdown_to_html_fragment(
        "Bravo [Acme](urn:li:organization:42) !", mentions=public_page_of
    )
    assert actual == '<p>Bravo <a href="https://exemple.fr/pages/42">Acme</a> !</p>'


def test_a_mention_never_links_to_what_runs_something():
    actual = parse_markdown_to_html_fragment(
        "Bravo [Acme](urn:li:organization:42) !", mentions=a_script
    )
    assert actual == "<p>Bravo @Acme !</p>"


def test_a_mention_whose_entity_is_not_given_goes_out_as_plain_text():
    actual = parse_markdown_to_html_fragment(
        "Merci [Claire](urn:li:person:kJCX3cn5)", mentions=entity_of
    )
    assert actual == "<p>Merci @Claire</p>"


def test_the_name_keeps_its_letters_and_case():
    actual = parse_markdown_to_html_fragment(
        "[ACME France](urn:li:organization:42)", mentions=entity_of
    )
    assert ">ACME France</a>" in actual


def test_a_mention_naming_nobody_writes_nothing():
    actual = parse_markdown_to_html_fragment(
        "Bravo [](urn:li:organization:42) !", mentions=entity_of
    )
    print(actual)
    assert "data-type" not in actual


def test_the_name_and_the_entity_are_escaped():
    actual = parse_markdown_to_html_fragment("[A&B](urn:li:organization:7)", mentions=entity_of)
    assert actual == '<p><a data-type="mention" data-entity-urn="company:7">A&amp;B</a></p>'


def test_strikethrough_as_its_look_alike_when_asked():
    actual = parse_markdown_to_html_fragment("Un ~~mot~~ ici.", unicode_strike=True)
    print(actual)
    assert actual == "<p>Un m̶o̶t̶ ici.</p>"


def test_otherwise_strikethrough_stays_a_tag():
    assert parse_markdown_to_html_fragment("Un ~~mot~~ ici.") == "<p>Un <s>mot</s> ici.</p>"


def test_a_list_of_tasks_as_a_paragraph_per_item_when_asked():
    actual = parse_markdown_to_html_fragment("- [ ] à faire\n- [x] fait", task_paragraphs=True)
    print(actual)
    assert actual == "<p>☐ à faire</p><p>☑ fait</p>"


def test_a_plain_item_among_tasks_keeps_its_marker_in_its_text():
    actual = parse_markdown_to_html_fragment("1. [ ] à faire\n2. ensuite", task_paragraphs=True)
    print(actual)
    assert actual == "<p>☐ à faire</p><p>2. ensuite</p>"


def test_a_list_without_tasks_stays_a_list():
    assert (
        parse_markdown_to_html_fragment("- un\n- deux", task_paragraphs=True)
        == "<ul><li>un</li><li>deux</li></ul>"
    )


# --- What the caller's attributes may hold ---
#
# A set breaking one rule is refused whole: the mention goes out as `@name`.
# The URNs end as the parity scenarios' do, which replay them on both sides.

HOSTILE = {
    "empty": {},
    "script": {"href": "  JaVa\tScRiPt:alert(1)"},
    "upper": {"HREF": "javascript:alert(1)"},
    "handler": {"href": "https://exemple.fr", "onclick": "alert(1)"},
    "name": {"x onmouseover=alert(1) y": "1"},
    "colon": {"xlink:href": "https://exemple.fr"},
    "source": {"src": "data:text/html,<script>alert(1)</script>"},
    "twice": {"href": "https://exemple.fr", "HREF": "https://exemple.fr"},
    "number": {"data-n": 3},
    "cased": {"Data-Entity": 'a"b<c>'},
}


def hostile(urn):
    return HOSTILE[urn.rsplit(":", 1)[-1]]


@pytest.mark.parametrize(
    "kind", ["empty", "script", "upper", "handler", "name", "colon", "source", "twice", "number"]
)
def test_attributes_breaking_a_rule_leave_the_name_as_plain_text(kind):
    actual = parse_markdown_to_html_fragment(
        f"Bravo [Acme](urn:li:organization:{kind}) !", mentions=hostile
    )
    print(actual)
    assert actual == "<p>Bravo @Acme !</p>"


def test_a_name_is_read_case_insensitively_and_written_lower_cased():
    actual = parse_markdown_to_html_fragment("[Acme](urn:li:organization:cased)", mentions=hostile)
    print(actual)
    assert actual == '<p><a data-entity="a&quot;b&lt;c&gt;">Acme</a></p>'


def test_no_attributes_at_all_is_plain_text_too():
    actual = parse_markdown_to_html_fragment("[Acme](urn:li:organization:empty)", mentions=hostile)
    assert actual == "<p>@Acme</p>"


# --- Strikethrough as its look-alike, across what is written apart ---


def test_the_space_beside_an_emoji_in_another_style_stays_unstruck():
    actual = parse_markdown_to_html_fragment("~~salut **👋** toi~~", unicode_strike=True)
    print(actual)
    assert actual == "<p>s̶a̶l̶u̶t̶ <strong>👋</strong> t̶o̶i̶</p>"


def test_code_inside_a_strikethrough_stays_as_written():
    actual = parse_markdown_to_html_fragment("~~un `code` ici~~", unicode_strike=True)
    print(actual)
    assert "<code>code</code>" in actual


def test_accents_are_composed_before_they_are_struck():
    decomposed = parse_markdown_to_html_fragment("~~e\u0301t\u00e9~~", unicode_strike=True)
    print(decomposed)
    assert decomposed == "<p>\u00e9\u0336t\u0336\u00e9\u0336</p>"


def test_the_stroke_goes_after_a_letter_and_its_accent():
    # `q` and its tilde have no composed form: the stroke goes after both
    actual = parse_markdown_to_html_fragment("~~q\u0303~~", unicode_strike=True)
    assert actual == "<p>q\u0303\u0336</p>"


# --- Lists of tasks as paragraphs ---


def test_a_plain_item_of_a_loose_list_keeps_its_marker():
    actual = parse_markdown_to_html_fragment("- [ ] a\n\n- b\n\n- [x] c", task_paragraphs=True)
    print(actual)
    assert actual == "<p>☐ a</p><p>• b</p><p>☑ c</p>"


def test_a_numbered_list_counts_from_zero_when_it_starts_there():
    actual = parse_markdown_to_html_fragment("0. [ ] a\n1. b", task_paragraphs=True)
    print(actual)
    assert actual == "<p>☐ a</p><p>1. b</p>"
