from inkletter.ast import *
from inkletter.visitors.tree import print_tree

# --- ImageRow: paragraph made only of images ---


def test_two_images_same_line_make_a_row(ast):
    doc = ast("![a](https://x.com/a.png) ![b](https://x.com/b.png)")
    print_tree(doc)
    assert len(doc.children) == 1

    row = doc.children[0]
    assert isinstance(row, ImageRow)
    assert [img.url for img in row.children] == [
        "https://x.com/a.png",
        "https://x.com/b.png",
    ]


def test_images_on_separate_lines_make_a_row(ast):
    doc = ast("![a](https://x.com/a.png)\n![b](https://x.com/b.png)")
    print_tree(doc)
    assert isinstance(doc.children[0], ImageRow)


def test_images_with_hard_breaks_make_a_row(ast):
    doc = ast("![a](https://x.com/a.png)  \n![b](https://x.com/b.png)")
    print_tree(doc)
    assert isinstance(doc.children[0], ImageRow)


def test_linked_image_counts_as_an_image(ast):
    doc = ast("[![a](https://x.com/a.png)](https://x.com) ![b](https://x.com/b.png)")
    print_tree(doc)

    row = doc.children[0]
    assert isinstance(row, ImageRow)
    assert isinstance(row.children[0], ImageLink)
    assert isinstance(row.children[1], Image)


def test_single_image_stays_an_image(ast):
    doc = ast("![a](https://x.com/a.png)")
    print_tree(doc)

    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert len(para.children) == 1
    assert isinstance(para.children[0], Image)


def test_single_image_with_trailing_space_loses_the_blank_filler(ast):
    doc = ast("![a](https://x.com/a.png) ")
    print_tree(doc)

    para = doc.children[0]
    assert isinstance(para, Paragraph)
    assert len(para.children) == 1
    assert isinstance(para.children[0], Image)


# --- MediaObject: one image beside its text ---


def test_leading_image_with_text_makes_a_media_object(ast):
    doc = ast("![Jean](https://x.com/j.png) Jean rejoint l'équipe.")
    print_tree(doc)

    media = doc.children[0]
    assert isinstance(media, MediaObject)
    assert media.side == "left"
    assert media.image.url == "https://x.com/j.png"
    assert len(media.children) == 1
    block = media.children[0]
    assert isinstance(block, BlockText)
    # the leftover separator whitespace is trimmed
    assert block.children[0].value == "Jean rejoint l'équipe."


def test_trailing_image_with_text_makes_a_right_media_object(ast):
    doc = ast("Jean rejoint l'équipe. ![Jean](https://x.com/j.png)")
    print_tree(doc)

    media = doc.children[0]
    assert isinstance(media, MediaObject)
    assert media.side == "right"
    assert media.children[0].children[-1].value == "Jean rejoint l'équipe."


def test_leading_linked_image_makes_a_media_object(ast):
    doc = ast("[![J](https://x.com/j.png)](https://x.com) Voir le profil.")
    print_tree(doc)

    media = doc.children[0]
    assert isinstance(media, MediaObject)
    assert isinstance(media.image, ImageLink)


def test_image_in_the_middle_stays_a_paragraph(ast):
    doc = ast("Avant ![a](https://x.com/a.png) après")
    print_tree(doc)
    assert isinstance(doc.children[0], Paragraph)


def test_two_images_with_text_stay_a_paragraph(ast):
    doc = ast("![a](https://x.com/a.png) texte ![b](https://x.com/b.png)")
    print_tree(doc)
    assert isinstance(doc.children[0], Paragraph)
