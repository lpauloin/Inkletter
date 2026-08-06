from inkletter.md_to_text import parse_markdown_to_text


def test_emphasis_markers_are_dropped():
    actual = parse_markdown_to_text(
        "Some *emphasis*, some **strong**, some ~~struck~~."
    )
    print(actual)
    assert actual == "Some emphasis, some strong, some struck.\n"


def test_code_span_is_literal():
    actual = parse_markdown_to_text("Type `make install` to finish.")
    print(actual)
    assert actual == "Type make install to finish.\n"


def test_link_renders_label_and_url():
    actual = parse_markdown_to_text("Visit [our site](https://example.com).")
    print(actual)
    assert actual == "Visit our site <https://example.com>.\n"


def test_link_with_label_equal_to_url():
    actual = parse_markdown_to_text("[https://example.com](https://example.com)")
    print(actual)
    assert actual == "https://example.com\n"


def test_autolink():
    actual = parse_markdown_to_text("Visit <https://example.com> now!")
    print(actual)
    assert actual == "Visit https://example.com now!\n"


def test_link_title_is_ignored():
    actual = parse_markdown_to_text('[site](https://example.com "A tooltip")')
    print(actual)
    assert actual == "site <https://example.com>\n"


def test_formatted_link_label_is_flattened():
    actual = parse_markdown_to_text("[the *full* guide](https://example.com)")
    print(actual)
    assert actual == "the full guide <https://example.com>\n"


def test_inline_html_tags_vanish():
    actual = parse_markdown_to_text("A <span>word</span> that matters<br>and the rest")
    print(actual)
    assert actual == "A word that mattersand the rest\n"
