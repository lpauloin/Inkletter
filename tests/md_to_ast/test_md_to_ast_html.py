from inkletter.ast import *
from inkletter.visitors.tree import print_tree


def test_block_html(ast):
    doc = ast("<div>hello</div>")
    print_tree(doc)
    assert isinstance(doc, Document)
    assert len(doc.children) == 1

    block = doc.children[0]
    assert isinstance(block, BlockHtml)
    assert block.value == "<div>hello</div>"


def test_multiline_block_html(ast):
    doc = ast("<table>\n  <tr><td>x</td></tr>\n</table>")
    print_tree(doc)

    block = doc.children[0]
    assert isinstance(block, BlockHtml)
    assert block.value == "<table>\n  <tr><td>x</td></tr>\n</table>"


def test_inline_html_in_paragraph(ast):
    doc = ast("Un <span>mot</span> important")
    print_tree(doc)
    assert isinstance(doc, Document)

    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert len(para.children) == 1
    assert isinstance(para.children[0], BlockText)

    block = para.children[0]
    values = [(type(c).__name__, c.value) for c in block.children]
    assert values == [
        ("LiteralText", "Un "),
        ("InlineHtml", "<span>"),
        ("LiteralText", "mot"),
        ("InlineHtml", "</span>"),
        ("LiteralText", " important"),
    ]


def test_inline_html_br(ast):
    doc = ast("ligne un<br>ligne deux")
    print_tree(doc)

    block = doc.children[0].children[0]
    assert isinstance(block, BlockText)
    assert any(isinstance(c, InlineHtml) and c.value == "<br>" for c in block.children)
