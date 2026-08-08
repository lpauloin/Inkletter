"""Image attributes: what the parser attaches, and what it lets through.

The grammar is strict on purpose. A brace block that is not an
attribute block must travel as ordinary text, with nobody having to
recognise it — that half of the file is what protects a document that
merely happens to contain braces.
"""

import pytest

from inkletter.ast import *
from inkletter.exceptions import MarkupError
from inkletter.link_attributes import parse_pairs
from inkletter.visitors.tree import TreeVisitor, print_tree


def only_image(doc):
    """The single image of a one-image document, wherever it landed."""
    node = doc.children[0]
    if isinstance(node, MediaObject):
        return node.image
    if isinstance(node, (ImageRow, Paragraph)):
        node = node.children[0]
    if isinstance(node, ImageLink):
        return node.img
    assert isinstance(node, Image), node
    return node


def sizing(doc):
    """The three attributes of that image, in a comparable shape."""
    attributes = only_image(doc).attributes
    return attributes.width, attributes.height, attributes.align


def tree(doc):
    visitor = TreeVisitor()
    visitor.visit(doc)
    return visitor.lines


# --- What the block attaches to ---


def test_attributes_reach_a_plain_image(ast):
    doc = ast("![Acme](logo.png){width=96px}")
    print_tree(doc)
    assert sizing(doc) == ("96px", None, None)


def test_attributes_reach_an_image_behind_a_link(ast):
    doc = ast("[![Acme](logo.png)](https://x.com){width=96px}")
    print_tree(doc)
    assert sizing(doc) == ("96px", None, None)


def test_both_spellings_of_a_linked_image_agree(ast):
    # the block glued to the image or to the link that wraps it: the
    # width ends up in the same place either way
    on_image = ast("[![a](i.png){width=320px}](https://x.com)")
    on_link = ast("[![a](i.png)](https://x.com){width=320px}")
    assert sizing(on_image) == sizing(on_link) == ("320px", None, None)


def test_a_label_holding_text_too_still_works(ast):
    doc = ast("[![a](i.png) and words](https://x.com){width=320px}")
    print_tree(doc)
    assert sizing(doc) == ("320px", None, None)


def test_a_text_link_is_not_a_target(ast):
    # nothing to size, so the braces stay what they were: text
    doc = ast("[terms](https://x.com){width=96px}")
    print_tree(doc)
    text = doc.children[0].children[0].children[-1]
    assert isinstance(text, LiteralText)
    assert text.value == "{width=96px}"


def test_a_space_detaches_the_block(ast):
    # the author's escape hatch, and Pandoc's
    doc = ast("![a](i.png) {width=96px}")
    print_tree(doc)
    assert sizing(doc) == (None, None, None)


def test_a_code_span_keeps_its_braces(ast):
    doc = ast("Write `{width=96px}` after an image")
    print_tree(doc)
    spans = [n for n in doc.children[0].children[0].children if isinstance(n, CodeSpan)]
    assert [span.code for span in spans] == ["{width=96px}"]


def test_an_image_without_a_block_carries_an_empty_value(ast):
    doc = ast("![Acme](logo.png)")
    attributes = only_image(doc).attributes
    assert not attributes
    assert sizing(doc) == (None, None, None)


# --- Every key ---


@pytest.mark.parametrize(
    "block, expected",
    [
        ("{width=96px}", ("96px", None, None)),
        ("{width=96}", ("96px", None, None)),  # a bare number means px
        ("{width=12.5px}", ("12.5px", None, None)),
        ("{width=320px}", ("320px", None, None)),
        ("{height=40px}", (None, "40px", None)),
        ("{align=left}", (None, None, "left")),
        ("{align=center}", (None, None, "center")),
        ("{align=right}", (None, None, "right")),
        ("{width=96px height=40px}", ("96px", "40px", None)),
        ("{align=left width=96px}", ("96px", None, "left")),
        ('{width="96px"}', ("96px", None, None)),
    ],
)
def test_accepted_blocks(ast, block, expected):
    doc = ast(f"![a](i.png){block}")
    print_tree(doc)
    assert sizing(doc) == expected


# --- What the grammar lets through as text ---


NOT_A_BLOCK = [
    "{beta}",
    "{see below}",
    "{1, 2, 3}",
    "{width=}",
    "{}",
    "{width=96px oops}",
    "{width=96 px}",  # the stray unit is a malformed token, not a bad value
]


@pytest.mark.parametrize("block", NOT_A_BLOCK)
def test_a_block_the_grammar_refuses_stays_text(ast, block):
    # no error: it may not be an attribute block at all, and raising
    # would break a document that merely contains braces
    doc = ast(f"![a](i.png){block}")
    print_tree(doc)
    assert sizing(doc) == (None, None, None)


@pytest.mark.parametrize("block", NOT_A_BLOCK)
def test_the_grammar_says_so_on_its_own(block):
    assert parse_pairs(block[1:-1]) is None


def test_braces_in_a_paragraph_are_left_alone(ast):
    doc = ast("A sentence {width=96px} with braces.")
    print_tree(doc)
    text = doc.children[0].children[0].children[0]
    assert text.value == "A sentence {width=96px} with braces."


# --- What the validation refuses ---


@pytest.mark.parametrize(
    "block, message",
    [
        (
            "{border-radius=4px}",
            "unknown image attribute 'border-radius'; the theme decides how images "
            "look. Attributes carry facts about the asset: width, height, align.",
        ),
        (
            "{style=color:red}",
            "unknown image attribute 'style'; the theme decides how images "
            "look. Attributes carry facts about the asset: width, height, align.",
        ),
        ("{width=96em}", "'width=96em' is not a length; mj-image sizes in px only"),
        ("{width=2in}", "'width=2in' is not a length; mj-image sizes in px only"),
        ("{height=10vw}", "'height=10vw' is not a length; mj-image sizes in px only"),
        ("{width=wide}", "'width=wide' is not a length; mj-image sizes in px only"),
        ("{align=top}", "'align=top' is not an alignment; use left, center, right"),
        ("{align=LEFT}", "'align=LEFT' is not an alignment; use left, center, right"),
        ("{width=96px width=48px}", "'width' is set twice"),
    ],
)
def test_refused_blocks(ast, block, message):
    with pytest.raises(MarkupError) as error:
        ast(f"![a](i.png){block}")
    assert str(error.value) == message


# --- The flag ---


def test_the_flag_off_leaves_the_braces_alone(ast):
    doc = ast("![a](i.png){width=96px}", link_attributes=False)
    print_tree(doc)
    # back to what it was: an image beside a run of text
    assert isinstance(doc.children[0], MediaObject)


def test_the_flag_changes_nothing_without_braces(ast):
    source = "# Title\n\n![a](i.png)\n\nText with **bold** and a [link](https://x.com)."
    assert tree(ast(source, link_attributes=True)) == tree(ast(source, link_attributes=False))
