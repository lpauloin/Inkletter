from inkletter.ast import *
from inkletter.visitors.tree import print_tree


def test_image_in_paragraph(ast):
    doc = ast('![alt text](https://picsum.photos/600/300 "Title")')
    print_tree(doc)
    assert isinstance(doc, Document)

    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert len(para.children) == 1

    img = para.children[0]
    assert isinstance(img, Image)
    assert img.url == "https://picsum.photos/600/300"
    assert img.title == "Title"
    assert isinstance(img.alt_text, LiteralText), img.alt_text
    assert img.alt_text.value == "alt text"


def test_image_alt_with_formatting(ast):
    doc = ast("![*bold* alt](https://picsum.photos/600/300)")
    print_tree(doc)
    assert isinstance(doc, Document)

    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert len(para.children) == 1

    img = para.children[0]
    assert isinstance(img, Image)
    assert img.url == "https://picsum.photos/600/300"
    assert isinstance(img.alt_text, LiteralText), img.alt_text
    assert img.alt_text.value == "bold alt"


def test_image_alt_with_nested_formatting(ast):
    doc = ast("![**Very** `important` ~~old~~ text](https://picsum.photos/600/300)")
    print_tree(doc)

    img = doc.children[0].children[0]
    assert isinstance(img, Image)
    assert isinstance(img.alt_text, LiteralText)
    assert img.alt_text.value == "Very important old text"


def test_image_in_link(ast):
    doc = ast("[![Alt](https://picsum.photos/600/300)](https://lien.com)")
    print_tree(doc)
    assert isinstance(doc, Document)

    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert len(para.children) == 1

    img_link = para.children[0]
    assert isinstance(img_link, ImageLink)
    assert img_link.href == "https://lien.com"
    assert isinstance(img_link.img, Image)
    img = img_link.img
    assert img.url == "https://picsum.photos/600/300"
    assert isinstance(img.alt_text, LiteralText)
    assert img.alt_text.value == "Alt"


def test_image_in_link_with_text(ast):
    doc = ast(
        "[![Alt](https://picsum.photos/600/300) This is an an additionnal text](https://lien.com)"
    )
    print_tree(doc)
    assert isinstance(doc, Document)

    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert len(para.children) == 1

    img_link = para.children[0]
    assert isinstance(img_link, ImageLink)
    assert img_link.href == "https://lien.com"
    assert isinstance(img_link.img, Image)
    img = img_link.img
    assert img.url == "https://picsum.photos/600/300"
    assert isinstance(img.alt_text, LiteralText)
    assert img.alt_text.value == "Alt"


def test_image_in_list(ast):
    doc = ast("- ![Étoile](https://picsum.photos/600/300) Élément")
    print_tree(doc)
    assert isinstance(doc, Document)

    lst = doc.children[0]
    assert isinstance(lst, List)
    assert len(lst.elements) == 1
    assert isinstance(lst.elements[0], ListItem)

    item = lst.elements[0]
    assert len(item.children) == 1
    assert isinstance(item.children[0], BlockText)

    block = item.children[0]
    assert len(block.children) == 2
    assert isinstance(block.children[0], Image)
    img = block.children[0]
    assert img.url == "https://picsum.photos/600/300"
    assert isinstance(img.alt_text, LiteralText)
    assert img.alt_text.value == "Étoile"

    assert isinstance(block.children[1], LiteralText)
    assert block.children[1].value == " Élément"


def test_image_in_blockquote(ast):
    doc = ast(
        """\
> ![Quote Icon](https://picsum.photos/600/300)
> Citation"""
    )
    print_tree(doc)
    assert isinstance(doc, Document)

    quote = doc.children[0]
    assert isinstance(quote, BlockQuote)
    assert len(quote.children) == 1
    assert isinstance(quote.children[0], Paragraph)

    para = quote.children[0]
    assert len(para.children) == 2
    assert isinstance(para.children[0], Image)

    img = para.children[0]
    assert img.url == "https://picsum.photos/600/300"
    assert isinstance(img.alt_text, LiteralText)
    assert img.alt_text.value == "Quote Icon"

    assert isinstance(para.children[1], BlockText)
    block = para.children[1]
    assert len(block.children) == 1
    assert isinstance(block.children[0], LiteralText)
    assert block.children[0].value == "Citation"


def test_image_in_table(ast):
    doc = ast(
        "| Produit | Image |\n"
        "|---------|-------|\n"
        "| Stylo | ![Stylo](https://picsum.photos/600/300) |"
    )
    print_tree(doc)
    assert isinstance(doc, Document)
    assert len(doc.children) == 1
    assert isinstance(doc.children[0], Table)

    table = doc.children[0]
    header = table.header
    rows = table.rows
    assert isinstance(header, TableHeader)
    assert len(header.headers) == 2
    assert isinstance(header.headers[0], TableHeaderCell)
    header_cell1 = header.headers[0]
    assert len(header_cell1.children) == 1
    assert isinstance(header_cell1.children[0], LiteralText)
    assert header_cell1.children[0].value == "Produit"
    assert isinstance(header.headers[1], TableHeaderCell)
    header_cell2 = header.headers[1]
    assert len(header_cell2.children) == 1
    assert isinstance(header_cell2.children[0], LiteralText)
    assert header_cell2.children[0].value == "Image"

    assert len(rows) == 1
    assert isinstance(rows[0], TableRow)
    assert len(rows[0].row) == 2

    assert isinstance(rows[0].row[0], TableCell)
    cell1 = rows[0].row[0]
    assert len(cell1.children) == 1
    assert isinstance(cell1.children[0], LiteralText)
    assert cell1.children[0].value == "Stylo"

    assert isinstance(rows[0].row[1], TableCell)
    cell2 = rows[0].row[1]
    assert len(cell2.children) == 1
    assert isinstance(cell2.children[0], Image)
    img = cell2.children[0]
    assert img.url == "https://picsum.photos/600/300"
    assert isinstance(img.alt_text, LiteralText)
    assert img.alt_text.value == "Stylo"


def test_image_in_heading(ast):
    doc = ast("## ![Icône](https://picsum.photos/600/300)")
    print_tree(doc)

    assert isinstance(doc, Document)
    assert len(doc.children) == 1
    assert isinstance(doc.children[0], Heading)
    heading = doc.children[0]
    assert heading.level == 2
    assert len(heading.children) == 1
    assert isinstance(heading.children[0], Image)
    img = heading.children[0]
    assert img.url == "https://picsum.photos/600/300"
    assert isinstance(img.alt_text, LiteralText)
    assert img.alt_text.value == "Icône"
