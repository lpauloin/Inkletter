from inkletter.md_to_text import parse_markdown_to_text


def test_table_is_ascii_aligned():
    markdown_input = """\
| Moment | Place |
|--------|-------|
| First glance | By the river |
| Farewell | Station |"""
    actual = parse_markdown_to_text(markdown_input)
    print(actual)
    assert actual == """\
Moment       | Place
-------------+-------------
First glance | By the river
Farewell     | Station
"""


def test_table_width_can_come_from_the_header():
    actual = parse_markdown_to_text("| A wide column | B |\n|---|---|\n| x | y |")
    print(actual)
    assert actual == """\
A wide column | B
--------------+--
x             | y
"""


def test_table_alignments():
    markdown_input = """\
| left | center | right |
|:-----|:------:|------:|
| a | b | c |"""
    actual = parse_markdown_to_text(markdown_input)
    print(actual)
    assert actual == """\
left | center | right
-----+--------+------
a    |   b    |     c
"""


def test_table_with_empty_cell():
    actual = parse_markdown_to_text("| A | B |\n|---|---|\n| x | |")
    print(actual)
    assert actual == """\
A | B
--+--
x |
"""


def test_table_cell_with_inline_formatting():
    actual = parse_markdown_to_text("| A |\n|---|\n| so **bold** |")
    print(actual)
    assert actual == """\
A
-------
so bold
"""


def test_table_inside_a_blockquote():
    actual = parse_markdown_to_text("> | A | B |\n> |---|---|\n> | 1 | 2 |")
    print(actual)
    assert actual == """\
> A | B
> --+--
> 1 | 2
"""
