"""The three styles a feed does not have, and every way they meet.

With `unicode_styling`, bold, italic and strikethrough become Unicode
look-alikes; without it they are dropped. What these tests pin is how the
styles combine — in any nesting order, whatever marks spell them — and what
a look-alike must never touch: a hashtag, a mention's marker, an address, a
call to action, an emoji.

The expected letters are built here from the code points themselves, not
from the tables under test.
"""

from itertools import permutations

import pytest

from inkletter import URLFactory, render_linkedin
from inkletter.md_to_linkedin import parse_markdown_to_linkedin
from inkletter.plugins.bare_domains import EXTENSIONS

STROKE = "̶"

# First lower-case and upper-case code point of each Unicode block.
BLOCKS = {
    frozenset(): None,
    frozenset({"bold"}): (0x1D5EE, 0x1D5D4),
    frozenset({"italic"}): (0x1D622, 0x1D608),
    frozenset({"bold", "italic"}): (0x1D656, 0x1D63C),
}


def looks(text, *styles):
    """`text` as the platform should receive it under `styles`."""
    block = BLOCKS[frozenset(styles) - {"strike"}]
    out = []
    for char in text:
        if block and "a" <= char <= "z":
            char = chr(block[0] + ord(char) - ord("a"))
        elif block and "A" <= char <= "Z":
            char = chr(block[1] + ord(char) - ord("A"))
        out.append(char + STROKE if "strike" in styles and char != "🎉" else char)
    return "".join(out)


def styled(markdown_text, **options):
    return parse_markdown_to_linkedin(markdown_text, unicode_styling=True, **options)


MARKS = {
    "*": {"bold": "**", "italic": "*", "strike": "~~"},
    "_": {"bold": "__", "italic": "_", "strike": "~~"},
}


def nested(word, order, family):
    """`word` wrapped in the marks of `order`, outermost first."""
    opening = "".join(MARKS[family][style] for style in order)
    closing = "".join(MARKS[family][style] for style in reversed(order))
    return f"{opening}{word}{closing}"


ORDERS = [order for size in (1, 2, 3) for order in permutations(("bold", "italic", "strike"), size)]


def styles_of(marks):
    styles = set()
    if "~~" in marks:
        styles.add("strike")
    stars = marks.replace("~", "")
    if len(stars) in (2, 3):
        styles.add("bold")
    if len(stars) in (1, 3):
        styles.add("italic")
    return styles


# --- Every combination, in every order, with either family of marks ---


@pytest.mark.parametrize("family", ["*", "_"])
@pytest.mark.parametrize("order", ORDERS, ids="+".join)
def test_styles_combine_whatever_is_outside(order, family):
    assert styled(nested("Mot", order, family)) == looks("Mot", *order)


@pytest.mark.parametrize("family", ["*", "_"])
@pytest.mark.parametrize("order", ORDERS, ids="+".join)
def test_without_substitutes_every_combination_is_plain_text(order, family):
    assert parse_markdown_to_linkedin(nested("Mot", order, family)) == "Mot"


# --- Bold and italic together ---


def test_bold_italic_has_its_own_letters():
    assert styled("***mot***") == "𝙢𝙤𝙩"


def test_italic_inside_bold_is_bold_italic_there_only():
    assert styled("**un *mot* fort**") == "𝘂𝗻 𝙢𝙤𝙩 𝗳𝗼𝗿𝘁"


def test_bold_inside_italic_is_bold_italic_there_only():
    assert styled("*un **mot** doux*") == "𝘶𝘯 𝙢𝙤𝙩 𝘥𝘰𝘶𝘹"


def test_marks_of_both_families_mix():
    assert styled("**_mot_**") == "𝙢𝙤𝙩"
    assert styled("_**mot**_") == "𝙢𝙤𝙩"


def test_a_style_closing_inside_another_keeps_the_rest():
    # `***mot** suite*`: bold italic on « mot », italic on « suite »
    assert (
        styled("***mot** suite*") == f"{looks('mot', 'bold', 'italic')} {looks('suite', 'italic')}"
    )


def test_bold_inside_bold_stays_bold():
    assert styled("**un __mot__ fort**") == looks("un mot fort", "bold")


def test_the_three_styles_at_once():
    assert styled("***~~mot~~***") == "𝙢̶𝙤̶𝙩̶"


def test_uppercase_has_its_look_alikes_too():
    assert styled("***ABC xyz***") == looks("ABC xyz", "bold", "italic")


# --- What a look-alike costs ---


@pytest.mark.parametrize(
    ("markdown_text", "units"),
    [
        ("**mot**", 6),
        ("*mot*", 6),
        ("***mot***", 6),
        ("~~mot~~", 6),
        ("**~~mot~~**", 9),
        ("***~~mot~~***", 9),
        ("**Étude 2026**", 14),
    ],
)
def test_a_look_alike_costs_what_the_platform_counts(markdown_text, units, measured):
    # two UTF-16 units per substituted letter; a stroke costs one more per
    # character; an accent or a digit costs itself
    assert measured(markdown_text, unicode_styling=True) == units


def test_the_count_is_the_length_of_what_goes_out(measured):
    markdown_text = "**un *mot* ~~barré~~** et ***tout***"
    assert (
        measured(markdown_text, unicode_styling=True)
        == len(styled(markdown_text).encode("utf-16-le")) // 2
    )


class Width(URLFactory):
    """Shortens nothing; declares the width a short link will have."""

    link_length = 26


def test_a_hashtag_in_a_style_costs_its_own_characters(measured):
    # « Parlons » in look-alikes, 14; the space, 1; the tag as written, 10
    assert measured("**Parlons #marketing**", unicode_styling=True) == 14 + 1 + 10


def test_a_split_hashtag_costs_its_own_characters(measured):
    assert measured("*#équipe_rh*", unicode_styling=True) == len("#équipe_rh")


def test_a_call_to_action_costs_its_label_unstyled_and_a_short_link(measured):
    # « En savoir plus : » is 17 plain characters, then the short link
    actual = measured(
        "**[En savoir plus](https://exemple.fr)**", unicode_styling=True, url_factory=Width()
    )
    assert actual == len("En savoir plus : ") + 26


def test_a_struck_emoji_costs_the_emoji_alone(measured):
    # o̶k̶ is 4 units and the space beside the emoji 1, its stroke skipped as
    # the emoji's is; 🎉 is 2 and takes none
    assert measured("~~ok 🎉~~", unicode_styling=True) == 5 + 2


def test_a_bare_address_in_bold_costs_a_short_link_and_nothing_for_its_marks(measured):
    assert measured("**https://exemple.fr**", unicode_styling=True, url_factory=Width()) == 26
    assert (
        measured("**voir https://exemple.fr**", unicode_styling=True, url_factory=Width())
        == 8 + 1 + 26
    )


def test_the_count_and_the_text_agree_on_every_new_behaviour(measured):
    # without a factory a link costs its address, so the count is the
    # UTF-16 length of what goes out, to the unit
    for markdown_text in [
        "**Parlons #marketing B2B**",
        "***~~mot~~*** et #tag",
        "**[En savoir plus](https://exemple.fr)** ~~vu 🎉~~",
        "*#équipe_rh* **https://exemple.fr**",
    ]:
        text = parse_markdown_to_linkedin(markdown_text, unicode_styling=True)
        units = len(text.encode("utf-16-le")) // 2
        assert measured(markdown_text, unicode_styling=True) == units, markdown_text


# --- Only letters have look-alikes ---


def test_accents_and_digits_stay_as_they_are():
    assert (
        styled("***Réglé 2026***")
        == f"{looks('R', 'bold', 'italic')}é{looks('gl', 'bold', 'italic')}é 2026"
    )


def test_an_emoji_stays_an_emoji_in_any_style():
    assert styled("***bravo*** 🎉") == f"{looks('bravo', 'bold', 'italic')} 🎉"


def test_look_alikes_already_typed_are_not_substituted_twice():
    assert styled("*𝗴𝗿𝗮𝘀*") == "𝗴𝗿𝗮𝘀"


# --- Strikethrough ---


def test_strikethrough_crosses_letters_digits_punctuation_and_spaces():
    assert styled("~~deux mots, 2 !~~") == "".join(char + STROKE for char in "deux mots, 2 !")


def test_strikethrough_crosses_accented_letters_once():
    assert styled("~~été~~") == f"é{STROKE}t{STROKE}é{STROKE}"


@pytest.mark.parametrize("emoji", ["🎉", "🇫🇷", "👍🏽", "👨‍👩‍👧", "❤️"])
def test_strikethrough_leaves_an_emoji_whole(emoji):
    # a stroke after a joiner, a variation selector or a skin tone breaks the
    # picture instead of crossing it out — and so does one on the space next
    # to it, which runs into the picture all the same
    assert styled(f"~~ok {emoji}~~") == f"o{STROKE}k{STROKE} {emoji}"


def test_a_space_between_two_struck_words_is_struck():
    assert styled("~~ok ko~~") == f"o{STROKE}k{STROKE} {STROKE}k{STROKE}o{STROKE}"


# --- A hashtag is never substituted ---


@pytest.mark.parametrize("marks", ["**", "*", "~~", "***", "**~~"])
def test_a_hashtag_inside_any_style_is_written_as_is(marks):
    closing = marks[::-1]
    assert styled(f"{marks}#marketing{closing}") == "#marketing"


def test_the_words_around_a_hashtag_keep_their_style():
    assert (
        styled("**Parlons #marketing B2B**")
        == f"{looks('Parlons', 'bold')} #marketing {looks('B', 'bold')}2{looks('B', 'bold')}"
    )


def test_an_accented_hashtag_is_one_too():
    assert styled("*#étude2026 et #équipe_rh*") == f"#étude2026 {looks('et', 'italic')} #équipe_rh"


def test_what_is_not_a_hashtag_is_styled():
    # digits only, or a `#` inside a word, is no tag
    assert styled("**#2026 C#**") == f"#2026 {looks('C', 'bold')}#"


def test_a_hashtag_after_punctuation_is_one():
    assert styled("**(#marketing)**") == "(#marketing)"


@pytest.mark.parametrize("tag", ["#équipe_rh", "#a_b_c", "#mot_clé_2026"])
def test_a_hashtag_the_parser_splits_on_underscores_is_still_one(tag):
    # the parser hands `#équipe_rh` over in pieces around each `_`
    assert styled(f"*{tag} ici*") == f"{tag} {looks('ici', 'italic')}"


def test_a_hashtag_does_not_run_into_the_next_line():
    assert styled("**#tag**\nsuite **gras**") == f"#tag\nsuite {looks('gras', 'bold')}"


def test_a_hashtag_does_not_run_into_the_next_paragraph():
    assert styled("**#tag**\n\n**gras**") == f"#tag\n\n{looks('gras', 'bold')}"


def test_a_hashtag_does_not_run_into_the_next_item():
    assert styled("- **#un**\n- **deux**") == f"• #un\n• {looks('deux', 'bold')}"


# --- A mention's marker is never substituted ---


@pytest.mark.parametrize("marks", ["**", "*", "~~", "***", "***~~"])
def test_a_mention_inside_any_style_keeps_its_marker(marks):
    closing = marks[::-1]
    actual = styled(f"{marks}merci [Croco.code](urn:li:organization:1){closing}")
    assert actual.endswith("@[urn:li:organization:1|Croco.code]")
    assert actual.startswith(looks("merci ", *styles_of(marks)))


# --- An address is never substituted; its label is ---


@pytest.mark.parametrize("marks", ["*", "***"])
def test_a_link_inside_a_style_keeps_its_address(marks):
    closing = marks[::-1]
    actual = styled(f"{marks}voir [le site](https://exemple.fr){closing}")
    assert actual == f"{looks('voir le site', *styles_of(marks))} : https://exemple.fr"


@pytest.mark.parametrize("marks", ["~~", "*~~"])
def test_a_struck_link_is_struck_on_its_words_only(marks):
    # the separator is the output's glue, not the author's words, and the
    # address must stay clean or it would stop resolving
    closing = marks[::-1]
    actual = styled(f"{marks}voir [le site](https://exemple.fr){closing}")
    assert actual == f"{looks('voir le site', *styles_of(marks))} : https://exemple.fr"


def test_a_bold_link_among_words_has_a_bold_label():
    assert styled("**voir [le site](https://exemple.fr) ici**") == (
        f"{looks('voir le site', 'bold')} : https://exemple.fr {looks('ici', 'bold')}"
    )


# --- A call to action is a line of text ---


def test_a_call_to_action_keeps_its_own_letters():
    assert (
        styled("**[En savoir plus](https://exemple.fr)**") == "En savoir plus : https://exemple.fr"
    )


def test_a_call_to_action_on_its_own_line_among_styled_text():
    actual = styled("Du **gras**.\n\n**[Réserver](https://exemple.fr/rdv)**")
    assert actual == f"Du {looks('gras', 'bold')}.\n\nRéserver : https://exemple.fr/rdv"


def test_an_italic_link_alone_is_no_call_to_action():
    assert (
        styled("*[le site](https://exemple.fr)*")
        == f"{looks('le site', 'italic')} : https://exemple.fr"
    )


# --- A bare address inside a style ---


class Recorder(URLFactory):
    """Shortens nothing; remembers what it was offered."""

    def __init__(self):
        self.offered = []

    def rewrite_link(self, url, is_button=False, is_bold=False):
        self.offered.append((url, is_bold))
        return url


@pytest.mark.parametrize(
    ("markdown_text", "styles"),
    [
        ("**https://exemple.fr**", {"bold"}),
        ("*https://exemple.fr*", {"italic"}),
        ("~~https://exemple.fr~~", {"strike"}),
        ("***https://exemple.fr***", {"bold", "italic"}),
        ("__https://exemple.fr__", {"bold"}),
    ],
)
def test_a_bare_address_in_a_style_loses_its_marks_not_its_end(markdown_text, styles):
    factory = Recorder()
    actual = parse_markdown_to_linkedin(markdown_text, unicode_styling=True, url_factory=factory)
    assert actual == "https://exemple.fr"
    assert factory.offered == [("https://exemple.fr", "bold" in styles)]


def test_a_bare_address_among_bold_words():
    factory = Recorder()
    actual = parse_markdown_to_linkedin(
        "**voir https://exemple.fr**.", unicode_styling=True, url_factory=factory
    )
    assert actual == f"{looks('voir', 'bold')} https://exemple.fr."
    assert factory.offered == [("https://exemple.fr", True)]


@pytest.mark.parametrize(
    ("markdown_text", "address"),
    [
        ("voir https://exemple.fr/a*b ici", "https://exemple.fr/a*b"),
        ("voir https://exemple.fr/un_chemin ici", "https://exemple.fr/un_chemin"),
        ("voir https://exemple.fr/page_ ici", "https://exemple.fr/page"),
        ("voir https://exemple.fr/page~ ici", "https://exemple.fr/page"),
        ("voir https://exemple.fr. Ensuite", "https://exemple.fr"),
        ("(voir http://a.fr/b) ensuite", "http://a.fr/b"),
        ("voir http://a.fr/b_(c) ensuite", "http://a.fr/b_(c)"),
        ("(voir http://a.fr/b_(c)) ensuite", "http://a.fr/b_(c)"),
        ("voir http://a.fr/b)) ensuite", "http://a.fr/b"),
    ],
)
def test_a_bare_address_keeps_its_inner_marks_and_drops_its_trailing_ones(markdown_text, address):
    factory = Recorder()
    parse_markdown_to_linkedin(markdown_text, url_factory=factory)
    assert factory.offered == [(address, False)]


# --- A domain written without its scheme ---
#
# `exemple.com` is a link to `https://exemple.com`: a feed makes it
# clickable whether or not the author wrote the scheme, so the factory is
# offered it like any other address.


@pytest.mark.parametrize(
    ("markdown_text", "address"),
    [
        # the name alone, wherever it stands
        ("exemple.com", "https://exemple.com"),
        ("voir exemple.com ici", "https://exemple.com"),
        ("👉Découvrez Exemple : exemple.com", "https://exemple.com"),
        ("👉exemple.com", "https://exemple.com"),
        ("l'app.exemple.com", "https://app.exemple.com"),
        ("«exemple.com»", "https://exemple.com"),
        ('"exemple.com"', "https://exemple.com"),
        ("voir\nexemple.com\nici", "https://exemple.com"),
        # only the extension is held to lower case
        ("voir Exemple.com ici", "https://Exemple.com"),
        ("voir EXEMPLE.com ici", "https://EXEMPLE.com"),
        # several labels, hyphens inside, digits
        ("voir app.exemple.com ici", "https://app.exemple.com"),
        ("voir exemple.co.uk ici", "https://exemple.co.uk"),
        ("voir mon-site.fr ici", "https://mon-site.fr"),
        ("voir xn--caf-dma.fr ici", "https://xn--caf-dma.fr"),
        ("voir 3suisses.fr ici", "https://3suisses.fr"),
        # `www.` says it, whatever the ending
        ("voir www.exemple.com ici", "https://www.exemple.com"),
        ("voir www.exemple.museum ici", "https://www.exemple.museum"),
        ("voir www.exemple.fr/page ici", "https://www.exemple.fr/page"),
        ("voir www.exemple.com.au ici", "https://www.exemple.com.au"),
        # what follows the name is the address too
        ("voir exemple.com/ ici", "https://exemple.com/"),
        ("voir exemple.com/tarifs ici", "https://exemple.com/tarifs"),
        ("voir exemple.com/tarifs?x=1 ici", "https://exemple.com/tarifs?x=1"),
        ("voir exemple.com/tarifs?x=1&y=2#prix ici", "https://exemple.com/tarifs?x=1&y=2#prix"),
        ("voir exemple.com?utm_source=linkedin ici", "https://exemple.com?utm_source=linkedin"),
        ("voir exemple.com#prix ici", "https://exemple.com#prix"),
        ("voir exemple.com:8080 ici", "https://exemple.com:8080"),
        ("voir exemple.com:8080/a ici", "https://exemple.com:8080/a"),
        ("voir exemple.com/a*b ici", "https://exemple.com/a*b"),
        ("voir exemple.com/un_chemin ici", "https://exemple.com/un_chemin"),
        ("voir exemple.com/a.zip ici", "https://exemple.com/a.zip"),
        # the sentence's punctuation stays the sentence's
        ("voir exemple.com. Ensuite", "https://exemple.com"),
        ("voir exemple.com, puis", "https://exemple.com"),
        ("voir exemple.com: la suite", "https://exemple.com"),
        ("voir exemple.com; la suite", "https://exemple.com"),
        ("tu connais exemple.com?", "https://exemple.com"),
        ("tu connais exemple.com ?", "https://exemple.com"),
        ("allez sur exemple.com!", "https://exemple.com"),
        ("voir exemple.com/tarifs?x=1. Ensuite", "https://exemple.com/tarifs?x=1"),
        ("tu as vu exemple.com/tarifs?", "https://exemple.com/tarifs"),
        ("allez sur exemple.com/tarifs!", "https://exemple.com/tarifs"),
        ("voir exemple.com/page_ ici", "https://exemple.com/page"),
        ("voir exemple.com/page~ ici", "https://exemple.com/page"),
        # an underscore is a mark beside the name, never a letter of it
        ("mon_site.com", "https://site.com"),
        ("\\_exemple.com", "https://exemple.com"),
        ("voir exemple.com\\_x ici", "https://exemple.com"),
        ("(exemple.com)", "https://exemple.com"),
        ("(voir exemple.com/tarifs) ensuite", "https://exemple.com/tarifs"),
        ("voir exemple.com/b_(c) ensuite", "https://exemple.com/b_(c)"),
        ("(voir exemple.com/b_(c)) ensuite", "https://exemple.com/b_(c)"),
        ("voir exemple.com/b)) ensuite", "https://exemple.com/b"),
    ],
)
def test_a_domain_without_its_scheme_is_a_link_to_it(markdown_text, address):
    factory = Recorder()
    parse_markdown_to_linkedin(markdown_text, url_factory=factory)
    assert factory.offered == [(address, False)]


@pytest.mark.parametrize("extension", EXTENSIONS)
def test_every_listed_extension_makes_a_link(extension):
    factory = Recorder()
    parse_markdown_to_linkedin(f"voir exemple.{extension} ici", url_factory=factory)
    assert factory.offered == [(f"https://exemple.{extension}", False)]


def test_the_listed_extensions_are_the_ones_agreed():
    # a closed list: one added or dropped is a decision, read here
    assert sorted(EXTENSIONS) == sorted(
        "com net org info biz io co ai app dev tech fr eu be ch lu ca uk de es it nl pt us".split()
    )


@pytest.mark.parametrize(
    "markdown_text",
    [
        # a space forgotten after a full stop: the extension is never a capital
        "C'est fini.De retour lundi",
        "C'est fini.Com",
        "EXEMPLE.COM",
        "exemple.com.La suite",
        # not an extension of the list — a file, a word, another country
        "readme.md",
        "node.js",
        "archive.zip",
        "script.py",
        "exemple.me",
        "voila.la",
        "exemple.museum",
        # the extension must end the name
        "exemple.community",
        "exemple.comme",
        "exemple.com2",
        "exemple.com-x",
        "exemple.com.zip",
        "exemple.com.au",
        # a mail address is not a page
        "a@exemple.com",
        "prenom.nom@exemple.com",
        "jean.fr@exemple.zz",
        # inside a word, a path or a longer name
        "-exemple.com",
        ".exemple.com",
        # a `#` is a tag's, or nothing: never the start of a name
        "#exemple.com",
        "a#exemple.com",
        "#tag#exemple.com",
        "/exemple.com",
        "chemin/exemple.com",
        "a-.io",
        # an accented name is written with its scheme
        "café.fr",
        "écafe.fr",
        # not a name at all
        "www",
        "www.exemple",
        "exemple .com",
        "exemple. com",
        "com",
        ".com",
        "1.5",
        "v1.2",
        "etc.",
        "p.ex.",
    ],
)
def test_what_only_looks_like_a_domain_stays_text(markdown_text):
    factory = Recorder()
    actual = parse_markdown_to_linkedin(markdown_text, url_factory=factory)
    assert factory.offered == []
    assert actual == markdown_text


def test_a_domain_in_a_code_span_stays_code():
    factory = Recorder()
    assert parse_markdown_to_linkedin("`exemple.com`", url_factory=factory) == "exemple.com"
    assert factory.offered == []


def test_a_domain_inside_an_address_is_that_address():
    factory = Recorder()
    parse_markdown_to_linkedin("voir https://exemple.com/a.com/b.fr ici", url_factory=factory)
    assert factory.offered == [("https://exemple.com/a.com/b.fr", False)]


def test_an_address_and_a_domain_are_two_links():
    factory = Recorder()
    parse_markdown_to_linkedin(
        "https://exemple.com/a et exemple.fr, www.b.org", url_factory=factory
    )
    assert factory.offered == [
        ("https://exemple.com/a", False),
        ("https://exemple.fr", False),
        ("https://www.b.org", False),
    ]


def test_a_domain_in_a_link_label_is_part_of_the_label():
    # a link holds no link: the label's domain is words, the target is the link
    factory = Recorder()
    actual = parse_markdown_to_linkedin("[voir exemple.com](https://autre.fr)", url_factory=factory)
    assert actual == "voir exemple.com : https://autre.fr"
    assert factory.offered == [("https://autre.fr", False)]


def test_a_domain_as_a_link_target_is_left_as_written():
    # the rule reads text, not targets: a target says its own scheme, or none
    factory = Recorder()
    parse_markdown_to_linkedin("[là](exemple.com)", url_factory=factory)
    assert factory.offered == [("exemple.com", False)]


@pytest.mark.parametrize(
    ("markdown_text", "styles"),
    [
        ("**exemple.com**", {"bold"}),
        ("*exemple.com*", {"italic"}),
        ("_exemple.com_", {"italic"}),
        ("~~exemple.com~~", {"strike"}),
        ("***exemple.com***", {"bold", "italic"}),
        ("__exemple.com__", {"bold"}),
        ("**exemple.com/tarifs**", {"bold"}),
    ],
)
def test_a_domain_in_a_style_loses_its_marks_and_says_its_bold(markdown_text, styles):
    factory = Recorder()
    actual = parse_markdown_to_linkedin(markdown_text, unicode_styling=True, url_factory=factory)
    address = "https://" + markdown_text.strip("*_~")
    assert actual == address
    assert factory.offered == [(address, "bold" in styles)]


def test_a_domain_among_bold_words():
    factory = Recorder()
    actual = parse_markdown_to_linkedin(
        "**voir exemple.com**.", unicode_styling=True, url_factory=factory
    )
    assert actual == f"{looks('voir', 'bold')} https://exemple.com."
    assert factory.offered == [("https://exemple.com", True)]


def test_a_domain_in_bold_costs_a_short_link_and_nothing_for_its_marks(measured):
    assert measured("**exemple.com**", unicode_styling=True, url_factory=Width()) == 26
    assert measured("**voir exemple.com**", unicode_styling=True, url_factory=Width()) == 8 + 1 + 26


# --- Styles in blocks ---


def test_styles_combine_in_a_heading():
    assert styled("# Titre ***fort***") == f"Titre {looks('fort', 'bold', 'italic')}"


def test_styles_combine_in_a_list():
    expected = f"• un {looks('point ', 'bold')}{looks('cl', 'bold', 'italic')}é\n• deux"
    assert styled("- un **point *clé***\n- deux") == expected


def test_styles_combine_in_a_quote():
    assert styled("> ***cité***") == f"> {looks('cit', 'bold', 'italic')}é"


def test_a_code_span_in_bold_takes_the_bold():
    assert styled("**du `code` ici**") == looks("du code ici", "bold")


# The ask is a bold link alone on its line; among words, bold is emphasis.


def test_a_bold_link_among_words_is_emphasis_and_takes_the_look_alikes():
    render = render_linkedin(
        "Lisez **[notre étude](https://exemple.fr/etude)** ici", unicode_styling=True
    )
    assert render.text == "Lisez 𝗻𝗼𝘁𝗿𝗲 é𝘁𝘂𝗱𝗲 : https://exemple.fr/etude ici"


def test_a_bold_link_among_words_warns_of_the_bold_it_loses():
    assert render_linkedin(
        "Lisez **[notre étude](https://exemple.fr/etude)** ici"
    ).unrendered_formatting


def test_a_bold_link_alone_on_its_line_is_the_ask_and_keeps_its_letters():
    render = render_linkedin(
        "Notre étude :\n**[La lire](https://exemple.fr/etude)**", unicode_styling=True
    )
    assert render.text == "Notre étude :\nLa lire : https://exemple.fr/etude"
    assert not render_linkedin("**[La lire](https://exemple.fr/etude)**").unrendered_formatting
