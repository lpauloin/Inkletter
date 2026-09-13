"""What the annotation says about the words: the styles in force around each
text, and where its hashtags are. An output that cannot draw a style — the
LinkedIn one, with its look-alikes — reads these rather than guessing."""

import pytest

from inkletter.ast import *


def texts(node):
    """Every text and code span under `node`, in reading order."""
    if isinstance(node, (LiteralText, CodeSpan)):
        return [node]
    return [found for child in node.get_children() for found in texts(child)]


def content(text):
    return text.value if isinstance(text, LiteralText) else text.code


def styles_by_text(doc):
    # the parser leaves empty texts between adjacent marks: they say nothing
    return {content(text): text.annotations.get("styles") for text in texts(doc) if content(text)}


def walk(node):
    yield node
    for child in node.get_children():
        yield from walk(child)


# --- Styles ---


def test_plain_text_carries_no_style(ast):
    assert styles_by_text(ast("Du texte.")) == {"Du texte.": None}


@pytest.mark.parametrize(
    ("markdown_text", "styles"),
    [
        ("**mot**", {"bold"}),
        ("*mot*", {"italic"}),
        ("~~mot~~", {"strikethrough"}),
        ("***mot***", {"bold", "italic"}),
        ("**_mot_**", {"bold", "italic"}),
        ("_**mot**_", {"bold", "italic"}),
        ("~~***mot***~~", {"bold", "italic", "strikethrough"}),
    ],
)
def test_a_text_carries_every_style_around_it(ast, markdown_text, styles):
    assert styles_by_text(ast(markdown_text)) == {"mot": frozenset(styles)}


def test_a_style_covers_its_own_words_only(ast):
    assert styles_by_text(ast("**un *mot* fort** et la suite")) == {
        "un ": frozenset({"bold"}),
        "mot": frozenset({"bold", "italic"}),
        " fort": frozenset({"bold"}),
        " et la suite": None,
    }


def test_a_code_span_carries_the_style_around_it(ast):
    assert styles_by_text(ast("**du `code`**"))["code"] == frozenset({"bold"})


def test_a_link_label_carries_the_style_around_it(ast):
    doc = ast("*voir [le site](https://exemple.fr)*")
    assert styles_by_text(doc) == {"voir ": frozenset({"italic"}), "le site": frozenset({"italic"})}


def test_a_mention_s_name_is_never_dressed(ast):
    # inside bold, the words around it are; the name is what the platform
    # matches on, and carries no style
    doc = ast("**merci [Croco.code](urn:li:organization:1) !**")
    assert styles_by_text(doc) == {
        "merci ": frozenset({"bold"}),
        "Croco.code": None,
        " !": frozenset({"bold"}),
    }


# --- A bold link on its own: the ask ---


def test_a_bold_link_alone_is_bold_for_the_factory_but_not_for_its_words(ast):
    doc = ast("**[En savoir plus](https://exemple.fr)**", bold_link_is_button=False)
    (link,) = [node for node in walk(doc) if isinstance(node, Link)]
    assert link.annotations["bold"] is True
    assert styles_by_text(doc) == {"En savoir plus": None}


def test_a_bold_link_among_words_is_bold_all_through(ast):
    doc = ast("**voir [le site](https://exemple.fr)**", bold_link_is_button=False)
    assert styles_by_text(doc) == {"voir ": frozenset({"bold"}), "le site": frozenset({"bold"})}


def test_other_styles_still_reach_a_lone_bold_link(ast):
    doc = ast("*__[Réserver](https://exemple.fr)__*", bold_link_is_button=False)
    assert styles_by_text(doc) == {"Réserver": frozenset({"italic"})}


# --- Hashtags ---
#
# A node of the tree, read at parse time before any mark inside it.


def hashtags(doc):
    return [node.name for node in walk(doc) if isinstance(node, Hashtag)]


def test_a_hashtag_is_a_node(ast):
    doc = ast("Nos #chiffres de 2026.")
    assert hashtags(doc) == ["chiffres"]
    assert styles_by_text(doc) == {"Nos ": None, " de 2026.": None}


def test_a_hashtag_with_underscores_is_one_node_not_an_italic(ast):
    # `_rh` would otherwise open an emphasis
    doc = ast("Bravo #équipe_rh et #a_b_c !")
    assert hashtags(doc) == ["équipe_rh", "a_b_c"]
    assert not [node for node in walk(doc) if isinstance(node, Emphasis)]


def test_a_hashtag_carries_no_style_of_its_own(ast):
    doc = ast("**Parlons #marketing**")
    assert hashtags(doc) == ["marketing"]
    (tag,) = [node for node in walk(doc) if isinstance(node, Hashtag)]
    assert "styles" not in tag.annotations


def test_a_heading_is_a_heading_and_may_hold_a_hashtag(ast):
    doc = ast("# Titre #tag")
    (heading,) = [node for node in walk(doc) if isinstance(node, Heading)]
    assert heading.level == 1
    assert hashtags(doc) == ["tag"]


def test_a_sharp_without_its_space_is_no_heading_but_a_hashtag(ast):
    doc = ast("#Titre")
    assert not [node for node in walk(doc) if isinstance(node, Heading)]
    assert hashtags(doc) == ["Titre"]


@pytest.mark.parametrize("text", ["#2026", "C#", "a#b", "&#39;", "##", "\\#pas", "# ", "#"])
def test_what_is_not_a_hashtag_makes_no_node(ast, text):
    assert hashtags(ast(text)) == []


@pytest.mark.parametrize(
    ("text", "names"),
    [
        ("(#marketing)", ["marketing"]),
        ("#un #deux", ["un", "deux"]),
        ("#étude2026", ["étude2026"]),
        ("#mot_clé_2026", ["mot_clé_2026"]),
    ],
)
def test_where_a_hashtag_starts(ast, text, names):
    assert hashtags(ast(text)) == names


def test_a_hashtag_colour_comes_from_the_theme(ast):
    from inkletter.theme import Hashtags, Theme

    plain = ast("Un #tag.")
    (tag,) = [node for node in walk(plain) if isinstance(node, Hashtag)]
    assert "hashtag_style" not in tag.annotations

    themed = ast("Un #tag.", theme=Theme(hashtags=Hashtags(color="#0a66c2")))
    (tag,) = [node for node in walk(themed) if isinstance(node, Hashtag)]
    assert tag.annotations["hashtag_style"] == "color: #0a66c2;"
