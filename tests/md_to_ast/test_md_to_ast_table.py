from inkletter.ast import *
from inkletter.visitors.tree import print_tree


def test_table(ast):
    doc = ast("""\
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
""")
    print_tree(doc)
    assert isinstance(doc, Document)

    table = doc.children[0]
    assert isinstance(table, Table)

    # --- Check header ---
    header = table.header
    assert isinstance(header, TableHeader)
    assert len(header.headers) == 2

    header_cell_1 = header.headers[0]
    header_cell_2 = header.headers[1]
    assert isinstance(header_cell_1, TableHeaderCell)
    assert isinstance(header_cell_2, TableHeaderCell)
    assert len(header_cell_1.children) == 1
    assert len(header_cell_2.children) == 1

    cell1 = header_cell_1.children[0]
    assert isinstance(cell1, LiteralText)
    assert cell1.value == "Header 1"

    cell2 = header_cell_2.children[0]
    assert isinstance(cell2, LiteralText)
    assert cell2.value == "Header 2"

    # --- Check body rows ---
    rows = table.rows
    assert len(rows) == 2

    expected_row_texts = [["Cell 1", "Cell 2"], ["Cell 3", "Cell 4"]]

    for row, expected_cells in zip(rows, expected_row_texts):
        assert isinstance(row, TableRow)
        assert row.is_header is False
        assert len(row.row) == 2

        for cell, expected_text in zip(row.row, expected_cells):
            assert isinstance(cell, TableCell)
            assert len(cell.children) == 1
            assert isinstance(cell.children[0], LiteralText)
            assert cell.children[0].value == expected_text


def test_table_with_alignment(ast):
    doc = ast("""\
| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Row 1        | Data           | More          |
| Row 2        | Data           | More          |
""")
    print_tree(doc)
    assert isinstance(doc, Document)

    table = doc.children[0]
    assert isinstance(table, Table)

    # --- Check header ---
    header = table.header
    assert isinstance(header, TableHeader)
    assert len(header.headers) == 3

    alignments = ["left", "center", "right"]
    header_texts = ["Left Aligned", "Center Aligned", "Right Aligned"]

    for cell, expected_text, expected_align in zip(
        header.headers, header_texts, alignments
    ):
        assert isinstance(cell, TableHeaderCell)
        assert cell.align == expected_align
        assert len(cell.children) == 1
        assert isinstance(cell.children[0], LiteralText)
        assert cell.children[0].value == expected_text

    # --- Check body rows ---
    rows = table.rows
    assert len(rows) == 2

    expected_body_texts = [["Row 1", "Data", "More"], ["Row 2", "Data", "More"]]

    for row, row_texts in zip(rows, expected_body_texts):
        assert isinstance(row, TableRow)
        assert row.is_header is False
        assert len(row.row) == 3

        for cell, expected_text, expected_align in zip(row.row, row_texts, alignments):
            assert isinstance(cell, TableCell)
            assert cell.align == expected_align
            assert len(cell.children) == 1
            assert isinstance(cell.children[0], LiteralText)
            assert cell.children[0].value == expected_text


def test_table_with_formated_cells(ast):
    doc = ast("""\
| ~~Header **1**~~                       | ~~Header **2**~~ |
|----------------------------------------|------------------|
| ~~**strong** and strike~~ cell         | **Cell 2**       |
""")
    print_tree(doc)
    assert isinstance(doc, Document)

    table = doc.children[0]
    assert isinstance(table, Table)

    # --- Check header ---
    header = table.header
    assert isinstance(header, TableHeader)
    assert len(header.headers) == 2

    header_cell1 = header.headers[0]
    assert isinstance(header_cell1, TableHeaderCell)
    assert len(header_cell1.children) == 1
    assert isinstance(header_cell1.children[0], StrikeThrough)
    strike = header_cell1.children[0]
    assert len(strike.children) == 2
    assert isinstance(strike.children[0], LiteralText)
    assert strike.children[0].value == "Header "
    assert isinstance(strike.children[1], Strong)
    assert len(strike.children[1].children) == 1
    assert isinstance(strike.children[1].children[0], LiteralText)
    assert strike.children[1].children[0].value == "1"

    header_cell2 = header.headers[1]
    assert isinstance(header_cell2, TableHeaderCell)
    assert len(header_cell2.children) == 1
    assert isinstance(header_cell2.children[0], StrikeThrough)
    strike = header_cell2.children[0]
    assert len(strike.children) == 2
    assert isinstance(strike.children[0], LiteralText)
    assert strike.children[0].value == "Header "
    assert isinstance(strike.children[1], Strong)
    assert len(strike.children[1].children) == 1
    assert isinstance(strike.children[1].children[0], LiteralText)
    assert strike.children[1].children[0].value == "2"

    # --- Check body rows ---
    rows = table.rows
    assert len(rows) == 1
    assert isinstance(rows[0], TableRow)
    assert len(rows[0].row) == 2

    assert isinstance(rows[0].row[0], TableCell)
    cell1 = rows[0].row[0]
    assert len(cell1.children) == 2
    assert isinstance(cell1.children[0], StrikeThrough)
    strike = cell1.children[0]
    assert len(strike.children) == 2
    assert isinstance(strike.children[0], Strong)
    assert len(strike.children[0].children) == 1
    assert isinstance(strike.children[0].children[0], LiteralText)
    assert strike.children[0].children[0].value == "strong"
    assert isinstance(strike.children[1], LiteralText)
    assert strike.children[1].value == " and strike"
    remain = cell1.children[1]
    assert isinstance(remain, LiteralText)
    assert remain.value == " cell"

    assert isinstance(rows[0].row[1], TableCell)
    cell2 = rows[0].row[1]
    assert len(cell2.children) == 1
    assert isinstance(cell2.children[0], Strong)
    assert len(cell2.children[0].children) == 1
    assert isinstance(cell2.children[0].children[0], LiteralText)
    assert cell2.children[0].children[0].value == "Cell 2"


def test_table_children_with_header_and_no_rows():
    # defensive: a header without rows must not crash ([header] + None)
    table = Table(header=TableHeader([]), rows=None)
    assert table.get_children() == [table.header]
    assert Table().get_children() == []
