from inkletter.ast import *
from inkletter.visitors.tree import print_tree


def test_unordered_list(ast):
    doc = ast("""\
- Item 1
- Item 2
""")
    print_tree(doc)
    assert isinstance(doc, Document)

    lst = doc.children[0]
    assert isinstance(lst, List)
    assert lst.ordered is False
    assert len(lst.elements) == 2

    item1 = lst.elements[0]
    assert isinstance(item1, ListItem)
    assert isinstance(item1.children[0], BlockText)
    assert len(item1.children[0].children) == 1
    assert isinstance(item1.children[0].children[0], LiteralText)
    assert item1.children[0].children[0].value == "Item 1"

    item2 = lst.elements[1]
    assert isinstance(item2, ListItem)
    assert isinstance(item2.children[0], BlockText)
    assert len(item2.children[0].children) == 1
    assert isinstance(item2.children[0].children[0], LiteralText)
    assert item2.children[0].children[0].value == "Item 2"


def test_ordered_list(ast):
    doc = ast("""\
1. First item
2. Second item
""")
    print_tree(doc)
    assert isinstance(doc, Document)

    lst = doc.children[0]
    assert isinstance(lst, List)
    assert lst.ordered is True
    assert len(lst.elements) == 2

    item1 = lst.elements[0]
    assert isinstance(item1, ListItem)
    assert isinstance(item1.children[0], BlockText)
    assert len(item1.children[0].children) == 1
    assert isinstance(item1.children[0].children[0], LiteralText)
    assert item1.children[0].children[0].value == "First item"

    item2 = lst.elements[1]
    assert isinstance(item2, ListItem)
    assert isinstance(item2.children[0], BlockText)
    assert len(item2.children[0].children) == 1
    assert isinstance(item2.children[0].children[0], LiteralText)
    assert item2.children[0].children[0].value == "Second item"


def test_task_list(ast):
    markdown = """\
- [x] Checked
- [ ] Not checked
"""

    doc = ast(markdown)
    print_tree(doc)

    # Check document
    assert isinstance(doc, Document)

    # Should be a list
    lst = doc.children[0]
    assert isinstance(lst, List)
    assert lst.ordered is False

    # Should have 2 TaskListItems
    assert len(lst.elements) == 2

    first_item = lst.elements[0]
    second_item = lst.elements[1]

    assert isinstance(first_item, TaskListItem)
    assert isinstance(second_item, TaskListItem)

    assert first_item.checked is True
    assert second_item.checked is False

    # Check element of first task
    element1 = first_item.children[0]
    assert isinstance(element1, BlockText)

    txt1 = element1.children[0]
    assert isinstance(txt1, LiteralText)
    assert txt1.value == "Checked"

    # Check element of second task
    element2 = second_item.children[0]
    assert isinstance(element2, BlockText)

    txt2 = element2.children[0]
    assert isinstance(txt2, LiteralText)
    assert txt2.value == "Not checked"


def test_task_list_nested_1(ast):
    markdown = """\
- [x] Checked
  1. Checked sub list Item 1
  2. Checked sub list Item 2
- [ ] Not checked
  1. Not checked sub list Item 1
  2. Not checked sub list Item 2
"""

    doc = ast(markdown)
    print_tree(doc)

    # --- Root list ---
    assert isinstance(doc, Document)
    main_list = doc.children[0]
    assert isinstance(main_list, List)
    assert len(main_list.elements) == 2

    # --- First TaskListItem ---
    first_task = main_list.elements[0]
    assert isinstance(first_task, TaskListItem)
    assert first_task.checked is True

    block = first_task.children[0]
    assert isinstance(block, BlockText)
    assert isinstance(block.children[0], LiteralText)
    assert block.children[0].value == "Checked"

    nested_list_1 = first_task.children[1]
    assert isinstance(nested_list_1, List)
    assert len(nested_list_1.elements) == 2

    expected_sub_items_1 = [
        "Checked sub list Item 1",
        "Checked sub list Item 2",
    ]
    for item, expected_text in zip(nested_list_1.elements, expected_sub_items_1):
        assert isinstance(item, ListItem)
        inner_block = item.children[0]
        assert isinstance(inner_block, BlockText)
        literal = inner_block.children[0]
        assert isinstance(literal, LiteralText)
        assert literal.value == expected_text

    # --- Second TaskListItem ---
    second_task = main_list.elements[1]
    assert isinstance(second_task, TaskListItem)
    assert second_task.checked is False

    block = second_task.children[0]
    assert isinstance(block, BlockText)
    assert isinstance(block.children[0], LiteralText)
    assert block.children[0].value == "Not checked"

    nested_list_2 = second_task.children[1]
    assert isinstance(nested_list_2, List)
    assert len(nested_list_2.elements) == 2

    expected_sub_items_2 = [
        "Not checked sub list Item 1",
        "Not checked sub list Item 2",
    ]
    for item, expected_text in zip(nested_list_2.elements, expected_sub_items_2):
        assert isinstance(item, ListItem)
        inner_block = item.children[0]
        assert isinstance(inner_block, BlockText)
        literal = inner_block.children[0]
        assert isinstance(literal, LiteralText)
        assert literal.value == expected_text


def test_task_list_nested_2(ast):
    markdown = """\
1. List Item 1
2. List Item 2
    - [x] Checked
    - [ ] Not checked
"""

    doc = ast(markdown)
    print_tree(doc)

    # --- Root ---
    assert isinstance(doc, Document)
    root_list = doc.children[0]
    assert isinstance(root_list, List)
    assert root_list.ordered is True
    assert not root_list.annotations.get("is_task_list")
    assert len(root_list.elements) == 2

    # --- First list item ---
    item_1 = root_list.elements[0]
    assert isinstance(item_1, ListItem)
    block_1 = item_1.children[0]
    assert isinstance(block_1, BlockText)
    assert isinstance(block_1.children[0], LiteralText)
    assert block_1.children[0].value == "List Item 1"

    # --- Second list item ---
    item_2 = root_list.elements[1]
    assert isinstance(item_2, ListItem)

    # First child = the text "List Item 2"
    block_2 = item_2.children[0]
    assert isinstance(block_2, BlockText)
    assert isinstance(block_2.children[0], LiteralText)
    assert block_2.children[0].value == "List Item 2"

    # Second child = nested task list
    nested_list = item_2.children[1]
    assert isinstance(nested_list, List)
    assert nested_list.ordered is False
    assert len(nested_list.elements) == 2

    first_task = nested_list.elements[0]
    second_task = nested_list.elements[1]

    assert isinstance(first_task, TaskListItem)
    assert first_task.checked is True
    task_block1 = first_task.children[0]
    assert isinstance(task_block1, BlockText)
    assert isinstance(task_block1.children[0], LiteralText)
    assert task_block1.children[0].value == "Checked"

    assert isinstance(second_task, TaskListItem)
    assert second_task.checked is False
    task_block2 = second_task.children[0]
    assert isinstance(task_block2, BlockText)
    assert isinstance(task_block2.children[0], LiteralText)
    assert task_block2.children[0].value == "Not checked"
