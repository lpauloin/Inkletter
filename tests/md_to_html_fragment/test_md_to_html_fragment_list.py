import pytest

from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment


def test_unordered_list():
    actual = parse_markdown_to_html_fragment("- one\n- two\n- three")
    print(actual)
    assert actual == "<ul><li>one</li><li>two</li><li>three</li></ul>"


def test_ordered_list():
    actual = parse_markdown_to_html_fragment("1. one\n2. two")
    print(actual)
    assert actual == "<ol><li>one</li><li>two</li></ol>"


def test_ordered_list_keeps_its_start():
    actual = parse_markdown_to_html_fragment("3. three\n4. four")
    print(actual)
    assert actual == '<ol start="3"><li>three</li><li>four</li></ol>'


def test_nested_list():
    actual = parse_markdown_to_html_fragment("- a\n  - a1\n  - a2\n- b")
    print(actual)
    assert actual == "<ul><li>a<ul><li>a1</li><li>a2</li></ul></li><li>b</li></ul>"


def test_task_list_uses_checkboxes():
    actual = parse_markdown_to_html_fragment("- [x] done\n- [ ] to do")
    print(actual)
    assert actual == "<ul><li>☑ done</li><li>☐ to do</li></ul>"


def test_mixed_task_and_normal_list():
    actual = parse_markdown_to_html_fragment("- [x] done\n- normal")
    print(actual)
    assert actual == "<ul><li>☑ done</li><li>normal</li></ul>"


def test_a_loose_list_keeps_its_paragraphs():
    actual = parse_markdown_to_html_fragment("- one\n\n- two")
    print(actual)
    assert actual == "<ul><li><p>one</p></li><li><p>two</p></li></ul>"


# --- Lists inside blocks, blocks inside lists ---


def test_a_list_inside_a_quote():
    actual = parse_markdown_to_html_fragment("> - one\n> - two")
    print(actual)
    assert actual == "<blockquote><ul><li>one</li><li>two</li></ul></blockquote>"


def test_a_quote_inside_a_list():
    actual = parse_markdown_to_html_fragment("- item\n\n  > quoted")
    print(actual)
    assert "<li>" in actual and "<blockquote><p>quoted</p></blockquote>" in actual


def test_code_inside_a_list():
    actual = parse_markdown_to_html_fragment("- item\n\n  ```\n  <b>x</b>\n  ```")
    print(actual)
    assert "<pre><code>&lt;b&gt;x&lt;/b&gt;\n</code></pre>" in actual


def test_a_deeply_nested_list():
    actual = parse_markdown_to_html_fragment("- 1\n  - 2\n    - 3\n      - 4")
    print(actual)
    assert actual.count("<ul>") == 4 and actual.count("</ul>") == 4


# --- Empty, blank and extreme inputs ---


# --- A list ends where its author stopped writing it ---


@pytest.mark.parametrize(
    ("markdown_text", "expected"),
    [
        ("- Étapes\nAprès", "<ul><li>Étapes</li></ul><p>Après</p>"),
        ("1. Étapes\nAprès", "<ol><li>Étapes</li></ol><p>Après</p>"),
        ("- [ ] Étapes\nAprès", "<ul><li>☐ Étapes</li></ul><p>Après</p>"),
    ],
)
def test_a_line_typed_after_an_item_is_a_block_of_its_own(markdown_text, expected):
    actual = parse_markdown_to_html_fragment(markdown_text)
    print(actual)
    assert actual == expected


def test_a_list_between_two_lines():
    actual = parse_markdown_to_html_fragment("Voici :\n- Un point\nMerci.")
    print(actual)
    assert actual == "<p>Voici :</p><ul><li>Un point</li></ul><p>Merci.</p>"


def test_lists_of_two_kinds_typed_line_after_line():
    actual = parse_markdown_to_html_fragment("- Un\n1. Deux\n- Trois")
    print(actual)
    assert actual == "<ul><li>Un</li></ul><ol><li>Deux</li></ol><ul><li>Trois</li></ul>"


def test_a_line_indented_under_an_item_is_still_the_item():
    actual = parse_markdown_to_html_fragment("- Étapes\n  suite")
    print(actual)
    assert actual == "<ul><li>Étapes<br>suite</li></ul>"


def test_a_block_after_a_blank_line_ends_the_list():
    actual = parse_markdown_to_html_fragment("1. un\n2. deux\n\n> Une citation")
    print(actual)
    assert actual == "<ol><li>un</li><li>deux</li></ol><blockquote><p>Une citation</p></blockquote>"
