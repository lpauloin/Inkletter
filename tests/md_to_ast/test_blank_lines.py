from inkletter.ast import BlankLine
from inkletter.md_to_ast import parse_markdown_to_ast


def blank_lines(document):
    return [node.lines for node in document.children if isinstance(node, BlankLine)]


def test_a_run_of_blank_lines_says_how_many_it_was():
    assert blank_lines(parse_markdown_to_ast("Un\n\nDeux")) == [1]
    assert blank_lines(parse_markdown_to_ast("Un\n\n\nDeux")) == [2]
    assert blank_lines(parse_markdown_to_ast("Un\n\n\n\n\nDeux")) == [4]


def test_a_blank_line_stands_between_two_blocks_rather_than_inside_one():
    document = parse_markdown_to_ast("Un\n\n\nDeux")
    assert [type(node).__name__ for node in document.children] == ["Paragraph", "BlankLine", "Paragraph"]
