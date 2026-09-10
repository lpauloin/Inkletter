from inkletter.ast import LineBreak, LiteralText, SoftBreak, Strong
from inkletter.visitors.trimmer import Trimmer

# What every output lays out on one line — a link's label, a mention's
# name, a table cell — is put on one line in the tree, right after
# parsing: a break inside becomes a space, the whitespace at either end
# goes. The renderers then have nothing to strip.


def first_inline(document):
    return document.children[0].children[0].children[0]


def reads(node):
    return "".join(child.value for child in node.children if isinstance(child, LiteralText))


# --- Breaks become spaces ---


def test_a_soft_break_in_a_label_becomes_a_space(ast):
    link = first_inline(ast("[un\nlien](https://x.test)"))
    print(link.children)
    assert not any(isinstance(child, SoftBreak) for child in link.children)
    assert reads(link) == "un lien"


def test_a_hard_break_in_a_label_becomes_a_space(ast):
    link = first_inline(ast("[un  \nlien](https://x.test)"))
    print(link.children)
    assert not any(isinstance(child, LineBreak) for child in link.children)
    assert reads(link) == "un lien"


def test_a_break_in_a_paragraph_is_left_alone(ast):
    # only what is laid out on one line is flattened
    text = ast("une ligne\nune autre").children[0].children[0]
    print(text.children)
    assert any(isinstance(child, SoftBreak) for child in text.children)


# --- Edges are trimmed ---


def test_a_padded_label_is_trimmed(ast):
    link = first_inline(ast("[ là ](https://x.test)"))
    assert reads(link) == "là"


def test_a_padded_mention_name_is_trimmed(ast):
    mention = first_inline(ast("[ Acme ](urn:li:organization:1)"))
    assert reads(mention) == "Acme"


def test_whitespace_only_edges_are_dropped_not_emptied(ast):
    # the spaces around the bold are nodes of their own; they go, rather
    # than staying as empty text
    link = first_inline(ast("[ **là** ](https://x.test)"))
    print(link.children)
    assert len(link.children) == 1
    assert isinstance(link.children[0], Strong)


def test_inner_whitespace_is_kept(ast):
    link = first_inline(ast("[un  lien](https://x.test)"))
    assert reads(link) == "un  lien"


# --- Cells ---


def test_a_cell_is_trimmed(ast):
    table = ast("|  a  | b |\n|---|---|\n|  1  | 2 |").children[0]
    header, row = table.header.headers, table.rows[0].row
    assert reads(header[0]) == "a"
    assert reads(row[0]) == "1"


def test_an_empty_cell_has_no_children(ast):
    table = ast("| a |  |\n|---|---|\n| 1 | |").children[0]
    assert table.header.headers[1].children == []
    assert table.rows[0].row[1].children == []


def test_a_link_inside_a_cell_is_trimmed_too(ast):
    table = ast("| [ là ](https://x.test) |\n|---|").children[0]
    link = table.header.headers[0].children[0]
    assert reads(link) == "là"


# --- The pass itself ---


def test_the_pass_is_idempotent(ast):
    document = ast("[ un\nlien ](https://x.test)")
    before = reads(first_inline(document))
    Trimmer().visit(document)
    assert reads(first_inline(document)) == before == "un lien"
