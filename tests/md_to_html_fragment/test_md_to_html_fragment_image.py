from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment

# An image is its alternative text: whatever renders a fragment never
# fetches anything for it.


def test_image_renders_its_alt():
    actual = parse_markdown_to_html_fragment("![Team picture](https://x.com/i.png)")
    print(actual)
    assert actual == "<p>Team picture</p>"


def test_image_without_alt_disappears():
    actual = parse_markdown_to_html_fragment("before\n\n![](https://x.com/i.png)\n\nafter")
    print(actual)
    assert "img" not in actual
    assert actual.startswith("<p>before</p>") and actual.endswith("<p>after</p>")


def test_linked_image_is_its_alt_as_the_link_it_was():
    actual = parse_markdown_to_html_fragment("[![Logo](https://x.com/l.png)](https://example.com)")
    print(actual)
    assert actual == '<p><a href="https://example.com">Logo</a></p>'


def test_linked_image_without_alt_leaves_nothing():
    actual = parse_markdown_to_html_fragment("[![](https://x.com/l.png)](https://example.com)")
    print(actual)
    assert actual == ""


def test_image_title_is_ignored():
    actual = parse_markdown_to_html_fragment('![Alt](https://x.com/i.png "Tooltip")')
    print(actual)
    assert actual == "<p>Alt</p>"


def test_an_image_never_fetches_whatever_its_address():
    actual = parse_markdown_to_html_fragment(
        '![x](https://evil.test/track.png) ![y](javascript:alert(1)) <img src="x" onerror="alert(1)">'
    )
    print(actual)
    assert "<img" not in actual and "onerror" not in actual and "evil.test" not in actual


# --- Tags meant to escape the page ---
