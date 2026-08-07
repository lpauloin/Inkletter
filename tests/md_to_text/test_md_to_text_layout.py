from inkletter.md_to_text import parse_markdown_to_text

URL = "https://example.com/go"


def test_button_is_a_cta_line():
    actual = parse_markdown_to_text(f"**[Get started]({URL})**")
    print(actual)
    assert actual == f"→ Get started : {URL}\n"


def test_button_disabled_renders_as_a_link():
    actual = parse_markdown_to_text(f"**[Get started]({URL})**", bold_link_is_button=False)
    print(actual)
    assert actual == f"Get started <{URL}>\n"


def test_image_row_is_one_line_per_image():
    actual = parse_markdown_to_text(
        "![Left view](https://x.com/a.png) ![Right view](https://x.com/b.png)"
    )
    print(actual)
    assert actual == "Left view\nRight view\n"


def test_image_row_with_a_linked_image():
    actual = parse_markdown_to_text(
        "[![Logo](https://x.com/l.png)](https://example.com) ![View](https://x.com/b.png)"
    )
    print(actual)
    assert actual == "Logo <https://example.com>\nView\n"


def test_media_object_stacks_alt_then_text():
    actual = parse_markdown_to_text("![Portrait](https://x.com/j.png) Jane joined the team.")
    print(actual)
    assert actual == "Portrait\n\nJane joined the team.\n"


def test_media_object_side_is_ignored():
    left = parse_markdown_to_text("![P](https://x.com/j.png) Some text.")
    right = parse_markdown_to_text("Some text. ![P](https://x.com/j.png)")
    print(left, right)
    assert left == "P\n\nSome text.\n"
    assert right == "P\n\nSome text.\n"
