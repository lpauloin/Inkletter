from inkletter.md_to_text import parse_markdown_to_text


def test_image_renders_its_alt():
    actual = parse_markdown_to_text("![Team picture](https://x.com/i.png)")
    print(actual)
    assert actual == "Team picture\n"


def test_image_without_alt_disappears():
    actual = parse_markdown_to_text("before\n\n![](https://x.com/i.png)\n\nafter")
    print(actual)
    assert actual == "before\n\nafter\n"


def test_linked_image_keeps_its_url():
    actual = parse_markdown_to_text(
        "[![Logo](https://x.com/l.png)](https://example.com)"
    )
    print(actual)
    assert actual == "Logo <https://example.com>\n"


def test_linked_image_without_alt_renders_the_url():
    actual = parse_markdown_to_text("[![](https://x.com/l.png)](https://example.com)")
    print(actual)
    assert actual == "https://example.com\n"


def test_image_title_is_ignored():
    actual = parse_markdown_to_text('![Alt](https://x.com/i.png "Tooltip")')
    print(actual)
    assert actual == "Alt\n"
