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
    assert [type(node).__name__ for node in document.children] == [
        "Paragraph",
        "BlankLine",
        "Paragraph",
    ]


def test_the_blank_lines_after_a_list_stand_between_it_and_what_follows():
    document = parse_markdown_to_ast("- a\n- b\n\n\n> c")
    assert [type(node).__name__ for node in document.children] == [
        "List",
        "BlankLine",
        "BlockQuote",
    ]
    assert blank_lines(document) == [2]


def test_the_blank_lines_inside_a_quote_are_the_quotes():
    (quote,) = parse_markdown_to_ast("> a\n>\n>\n> b").children
    assert blank_lines(quote) == [2]


def test_the_blank_lines_after_an_indented_code_block_are_counted():
    assert blank_lines(parse_markdown_to_ast("    code\n\n\nAprès")) == [2]


def test_the_lines_a_document_opens_and_ends_on_are_counted():
    document = parse_markdown_to_ast("\n\nUn\n\n\n")
    assert [type(node).__name__ for node in document.children] == [
        "BlankLine",
        "Paragraph",
        "BlankLine",
    ]
    assert blank_lines(document) == [2, 2]
