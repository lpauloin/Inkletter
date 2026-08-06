import mistune

from inkletter.ast import *
from inkletter.md_to_ast import ASTRenderer
from inkletter.scope import ScopeStack
from inkletter.theme import DEFAULT_THEME
from inkletter.visitors.annotation import Annotation
from inkletter.visitors.merger import BlockTextMerger
from inkletter.visitors.tree import print_tree


def generate_ast(markdown_input):
    renderer = ASTRenderer()
    markdown = mistune.create_markdown(
        renderer=renderer,
        plugins=[
            "table",
            "strikethrough",
            "task_lists",
        ],
    )
    ast = markdown(markdown_input)
    Annotation(DEFAULT_THEME).visit(ast, scope=ScopeStack())
    print("AST:")
    print_tree(ast)
    return ast


def merge_ast(ast):
    splitter = BlockTextMerger()
    splitter.visit(ast, scope=None)
    print("AST after splitting:")
    print_tree(ast)
    return ast


def test_merge_text():
    markdown_input = """\
This is a text
This is anoter text
"""

    # === AST BEFORE ===
    ast = generate_ast(markdown_input)
    assert isinstance(ast, Document)
    assert len(ast.children) == 1
    paragraph = ast.children[0]
    assert isinstance(paragraph, Paragraph)
    assert len(paragraph.children) == 3  # LiteralText, SoftBreak, LiteralText
    assert isinstance(paragraph.children[0], LiteralText)
    assert paragraph.children[0].value == "This is a text"
    assert isinstance(paragraph.children[1], SoftBreak)
    assert isinstance(paragraph.children[2], LiteralText)
    assert paragraph.children[2].value == "This is anoter text"

    # === AST AFTER MERGE ===
    merged_ast = merge_ast(ast)
    assert isinstance(ast, Document)
    assert len(ast.children) == 1
    paragraph = merged_ast.children[0]
    assert isinstance(paragraph, Paragraph)
    assert len(paragraph.children) == 1
    block = paragraph.children[0]
    assert isinstance(block, BlockText)
    assert len(block.children) == 3
    assert isinstance(block.children[0], LiteralText)
    assert block.children[0].value == "This is a text"
    assert isinstance(block.children[1], SoftBreak)
    assert isinstance(block.children[2], LiteralText)
    assert block.children[2].value == "This is anoter text"
