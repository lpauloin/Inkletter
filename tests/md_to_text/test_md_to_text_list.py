from inkletter.md_to_text import parse_markdown_to_text


def test_unordered_list():
    actual = parse_markdown_to_text("- one\n- two\n- three")
    print(actual)
    assert actual == "- one\n- two\n- three\n"


def test_ordered_list():
    actual = parse_markdown_to_text("1. one\n2. two")
    print(actual)
    assert actual == "1. one\n2. two\n"


def test_ordered_list_keeps_its_start():
    actual = parse_markdown_to_text("3. three\n4. four")
    print(actual)
    assert actual == "3. three\n4. four\n"


def test_nested_list_is_indented():
    actual = parse_markdown_to_text("- a\n  - a1\n  - a2\n- b")
    print(actual)
    assert actual == "- a\n  - a1\n  - a2\n- b\n"


def test_task_list_uses_ascii_checkboxes():
    actual = parse_markdown_to_text("- [x] done\n- [ ] to do")
    print(actual)
    assert actual == "[x] done\n[ ] to do\n"


def test_mixed_task_and_normal_list():
    actual = parse_markdown_to_text("- [x] done\n- normal")
    print(actual)
    assert actual == "[x] done\n- normal\n"
