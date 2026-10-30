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


def test_a_loose_list_reads_as_one_block():
    assert parse_markdown_to_text("- one\n\n- two\n- three") == "- one\n- two\n- three\n"


# --- A list ends where its author stopped writing it ---


def test_a_line_typed_after_an_item_is_a_block_of_its_own():
    actual = parse_markdown_to_text("- Étapes\nAprès")
    print(actual)
    assert actual == "- Étapes\n\nAprès\n"


def test_a_list_between_two_lines():
    actual = parse_markdown_to_text("Voici :\n- Un point\nMerci.")
    print(actual)
    assert actual == "Voici :\n\n- Un point\n\nMerci.\n"


def test_lists_of_two_kinds_typed_line_after_line():
    actual = parse_markdown_to_text("- Un\n1. Deux\n- Trois")
    print(actual)
    assert actual == "- Un\n\n1. Deux\n\n- Trois\n"


def test_a_line_indented_under_an_item_is_still_the_item():
    actual = parse_markdown_to_text("- Étapes\n  suite")
    print(actual)
    assert actual == "- Étapes\n  suite\n"


def test_a_list_starting_at_zero_says_zero():
    assert parse_markdown_to_text("0. zéro\n1. un") == "0. zéro\n1. un\n"


def test_a_box_in_a_numbered_list_keeps_its_rank_as_the_mail_counts_it():
    assert parse_markdown_to_text("1. [ ] a\n2. b") == "[ ] a\n2. b\n"


def test_an_image_in_an_item_adds_no_blank_line():
    assert parse_markdown_to_text("- a\n- ![a](https://i.com/a.png)\n- b") == "- a\n- a\n- b\n"


def test_an_empty_item_ends_on_its_marker_line():
    assert parse_markdown_to_text("-\n- b") == "-\n- b\n"
    assert parse_markdown_to_text("1.\n2. b") == "1.\n2. b\n"


def test_a_quote_opening_an_item_marks_its_first_line_too():
    assert parse_markdown_to_text("- > a\n  > b") == "- > a\n  > b\n"


def test_an_item_whose_first_block_writes_nothing_keeps_its_words_on_its_marker():
    assert parse_markdown_to_text("-\n  a") == "- a\n"
    assert parse_markdown_to_text("- <!-- c -->\n  a") == "- a\n"
    assert parse_markdown_to_text("- \\\n  a") == "- a\n"


def test_quotes_opening_an_item_mark_its_first_line_each():
    assert parse_markdown_to_text("- > > a\n  > > b") == "- > > a\n  > > b\n"


def test_a_block_showing_nothing_leaves_no_mark_on_an_item():
    assert parse_markdown_to_text("- >\n\n  a") == "- a\n"
    assert parse_markdown_to_text("- ![](https://i.com/x.png)\n\n  a") == "- a\n"
    assert parse_markdown_to_text("- >\n  > #\n  > a") == "- > a\n"
