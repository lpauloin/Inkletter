from inkletter.ast import *
from inkletter.visitors.tree import print_tree

URL = "https://exemple.com/go"

# --- Button created ---


def test_bold_link_alone_makes_a_button(ast):
    doc = ast(f"**[Get started]({URL})**")
    print_tree(doc)
    assert len(doc.children) == 1

    button = doc.children[0]
    assert isinstance(button, Button)
    assert button.href == URL
    assert button.title is None
    assert isinstance(button.children[0], LiteralText)
    assert button.children[0].value == "Get started"


def test_button_with_surrounding_blanks(ast):
    doc = ast(f"  **[Go]({URL})**  ")
    assert isinstance(doc.children[0], Button)


def test_button_keeps_the_link_title(ast):
    doc = ast(f'**[Go]({URL} "Mon titre")**')
    button = doc.children[0]
    assert isinstance(button, Button)
    assert button.title == "Mon titre"


def test_button_label_may_contain_emphasis_and_code(ast):
    doc = ast(f"**[*Vite* `go`]({URL})**")
    print_tree(doc)
    button = doc.children[0]
    assert isinstance(button, Button)
    kinds = [type(c) for c in button.children]
    assert Emphasis in kinds
    assert CodeSpan in kinds


# --- Not a button ---


def test_plain_link_alone_stays_a_paragraph(ast):
    doc = ast(f"[Go]({URL})")
    print_tree(doc)
    assert isinstance(doc.children[0], Paragraph)


def test_bold_link_with_text_stays_a_paragraph(ast):
    doc = ast(f"**[Go]({URL})** maintenant")
    assert isinstance(doc.children[0], Paragraph)


def test_two_bold_links_stay_a_paragraph(ast):
    doc = ast(f"**[Go]({URL})** **[Stop]({URL})**")
    assert isinstance(doc.children[0], Paragraph)


def test_bold_without_link_stays_a_paragraph(ast):
    doc = ast("**Juste du gras**")
    assert isinstance(doc.children[0], Paragraph)


def test_bold_with_link_and_text_inside_stays_a_paragraph(ast):
    doc = ast(f"**voir [Go]({URL})**")
    assert isinstance(doc.children[0], Paragraph)


def test_bold_image_link_is_never_a_button(ast):
    doc = ast(f"![i](https://x.com/i.png)")
    doc = ast(f"**[![i](https://x.com/i.png)]({URL})**")
    print_tree(doc)
    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert not isinstance(para, Button)


def test_bold_link_with_nested_image_is_never_a_button(ast):
    doc = ast(f"**[*a ![i](https://x.com/i.png)* b]({URL})**")
    assert isinstance(doc.children[0], Paragraph)


def test_bold_link_in_list_item_stays_inline(ast):
    doc = ast(f"- **[Go]({URL})**")
    print_tree(doc)
    lst = doc.children[0]
    assert isinstance(lst, List)
    item_block = lst.elements[0].children[0]
    assert isinstance(item_block, BlockText)
    assert isinstance(item_block.children[0], Strong)


def test_bold_link_in_blockquote_stays_inline(ast):
    doc = ast(f"> **[Go]({URL})**")
    quote = doc.children[0]
    assert isinstance(quote, BlockQuote)


def test_bold_link_in_table_cell_stays_inline(ast):
    doc = ast(f"| A |\n|---|\n| **[Go]({URL})** |")
    assert isinstance(doc.children[0], Table)


# --- The conversion parameter ---


def test_bold_link_is_button_disabled(ast):
    doc = ast(f"**[Go]({URL})**", bold_link_is_button=False)
    print_tree(doc)
    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert isinstance(para.children[0], BlockText)
    assert isinstance(para.children[0].children[0], Strong)
