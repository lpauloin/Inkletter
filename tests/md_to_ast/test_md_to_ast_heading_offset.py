"""The heading offset, moved once in the tree: every output reads the
level it became, held between 1 and 6."""

import inspect

import pytest

from inkletter.ast import BlockQuote, Heading
from inkletter.md_to_ast import parse_markdown_to_ast
from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment
from inkletter.md_to_linkedin import parse_markdown_to_linkedin, render_linkedin


def levels(node):
    found = [node.level] if isinstance(node, Heading) else []
    for child in node.get_children():
        found += levels(child)
    return found


@pytest.mark.parametrize(
    ("source", "offset", "expected"),
    [
        ("## A\n\n### B", -1, [1, 2]),
        ("# A\n\n###### B", -1, [1, 5]),
        ("# A\n\n##### B", 2, [3, 6]),
        ("## A", 0, [2]),
    ],
)
def test_every_heading_is_moved_and_held_between_1_and_6(source, offset, expected):
    assert levels(parse_markdown_to_ast(source, heading_offset=offset)) == expected


def test_a_heading_inside_a_quote_is_moved_too():
    ast = parse_markdown_to_ast("> ## Quoted", heading_offset=-1)
    quote = next(child for child in ast.get_children() if isinstance(child, BlockQuote))
    assert levels(quote) == [1]


@pytest.mark.parametrize("render", [render_linkedin, parse_markdown_to_linkedin])
def test_the_post_shows_no_heading_and_takes_no_offset(render):
    assert "heading_offset" not in inspect.signature(render).parameters


@pytest.mark.parametrize("offset", [1.5, True, "1", None])
def test_an_offset_that_is_no_integer_is_refused(offset):
    with pytest.raises(TypeError, match="^heading_offset must be an integer$"):
        parse_markdown_to_ast("## A", heading_offset=offset)


@pytest.mark.parametrize("offset", [1.5, True])
def test_the_fragment_refuses_it_as_the_tree_does(offset):
    with pytest.raises(TypeError, match="^heading_offset must be an integer$"):
        parse_markdown_to_html_fragment("## A", heading_offset=offset)
