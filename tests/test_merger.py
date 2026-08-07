import mistune

from inkletter.ast import *
from inkletter.md_to_ast import ASTRenderer
from inkletter.visitors.scope import ScopeStack
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
    Annotation(DEFAULT_THEME).visit(ast)
    print("AST:")
    print_tree(ast)
    return ast


def merge_ast(ast):
    splitter = BlockTextMerger()
    splitter.visit(ast)
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


def test_terminals_are_stripped_at_both_edges_of_each_group():
    # two inline groups split by an image: each flush must clean its own
    # buffer (the helpers used to close over the outer one by accident)
    ast = generate_ast("avant  \n![i](https://x.com/i.png)\nmilieu  \nfin")
    merged = merge_ast(ast)
    para = merged.children[0]

    kinds = [type(c).__name__ for c in para.children]
    assert kinds == ["BlockText", "Image", "BlockText"]
    first, _, second = para.children
    assert not isinstance(first.children[-1], TextTerminal)
    assert not isinstance(second.children[0], TextTerminal)


# --- What a scope is made of ---


def test_scope_records_the_types_living_below_it():
    scope = ScopeStack()
    root, child, grandchild = object(), object(), object()
    scope.push(root)
    scope.record_types()
    scope.push(child)
    scope.push(grandchild)
    assert scope.types() == {object}
    scope.pop(grandchild)
    scope.pop(child)
    assert scope.types() == {object}
    scope.pop(root)


def test_a_sibling_never_inherits_what_the_previous_one_held():
    # the recording dies with the scope that asked for it
    scope = ScopeStack()
    root = object()
    scope.push(root)
    seen = []
    for _ in range(2):
        watcher = object()
        scope.push(watcher)
        scope.record_types()
        scope.push(object())
        scope.pop(scope.stack[-1]["node"])
        seen.append(scope.types())
        scope.pop(watcher)
    assert seen[0] == seen[1] == {object}
    scope.pop(root)


def test_a_value_set_above_is_filled_in_from_below():
    # the other way round the one-way street: no new API, just a
    # container the scope above owns and descendants fill in
    scope = ScopeStack()
    root, leaf = object(), object()
    scope.push(root)
    scope.set("collected", [])
    scope.push(leaf)
    scope.get("collected").append("from below")
    scope.pop(leaf)
    assert scope.get("collected") == ["from below"]
    scope.pop(root)


def test_types_is_empty_when_nobody_records():
    scope = ScopeStack()
    node = object()
    scope.push(node)
    assert scope.types() == set()
    scope.pop(node)
