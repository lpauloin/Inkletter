from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment


def test_table():
    actual = parse_markdown_to_html_fragment(
        "| Moment | Place |\n|--------|-------|\n| First glance | By the river |"
    )
    print(actual)
    assert actual == (
        "<table><thead><tr><th>Moment</th><th>Place</th></tr></thead>"
        "<tbody><tr><td>First glance</td><td>By the river</td></tr></tbody></table>"
    )


def test_table_alignments():
    actual = parse_markdown_to_html_fragment(
        "| left | center | right |\n|:-----|:------:|------:|\n| a | b | c |"
    )
    print(actual)
    assert '<th style="text-align: left">left</th>' in actual
    assert '<td style="text-align: center">b</td>' in actual
    assert '<td style="text-align: right">c</td>' in actual


def test_table_with_empty_cell():
    actual = parse_markdown_to_html_fragment("| A | B |\n|---|---|\n| x | |")
    print(actual)
    assert "<tr><td>x</td><td></td></tr>" in actual


def test_table_cell_with_inline_formatting():
    actual = parse_markdown_to_html_fragment("| A |\n|---|\n| so **bold** |")
    print(actual)
    assert "<td>so <strong>bold</strong></td>" in actual


def test_table_inside_a_blockquote():
    actual = parse_markdown_to_html_fragment("> | A | B |\n> |---|---|\n> | 1 | 2 |")
    print(actual)
    assert actual.startswith("<blockquote><table>")
    assert actual.endswith("</table></blockquote>")
