"""A picture standing as a block: its title said under it, laid small,
inside its link; headings moved by an offset."""

from inkletter import parse_markdown_to_mjml


def body_of(mjml):
    return mjml.split("<mj-body", 1)[1].split("</mj-body>", 1)[0]


def test_a_lone_image_says_its_title_under_it():
    body = body_of(parse_markdown_to_mjml('![The stand](https://x.com/s.jpg "Thursday morning")'))
    print(body)
    assert '<mj-image src="https://x.com/s.jpg" alt="The stand" title="Thursday morning"/>' in body
    assert body.index("<mj-image") < body.index("Thursday morning\n") < body.index("</mj-text>")


def test_an_image_without_title_has_no_caption():
    body = body_of(parse_markdown_to_mjml("![The stand](https://x.com/s.jpg)"))
    assert "mj-text" not in body


def test_an_image_laid_small_takes_the_theme_s_narrower_width():
    body = body_of(parse_markdown_to_mjml("![The stand](https://x.com/s.jpg){size=small}"))
    print(body)
    assert 'width="360px"' in body


def test_a_width_of_its_own_wins_over_small():
    body = body_of(
        parse_markdown_to_mjml("![The stand](https://x.com/s.jpg){size=small width=200}")
    )
    assert 'width="200px"' in body and "360px" not in body


def test_a_linked_image_keeps_its_link_and_says_its_title_under_it():
    body = body_of(
        parse_markdown_to_mjml('[![Logo](https://x.com/l.png "Our site")](https://example.com)')
    )
    print(body)
    assert 'href="https://example.com"' in body
    assert "Our site\n" in body and "<mj-text" in body


def test_images_in_a_row_keep_their_titles_as_tooltips():
    body = body_of(
        parse_markdown_to_mjml('![A](https://x.com/a.png "One") ![B](https://x.com/b.png "Two")')
    )
    print(body)
    assert "mj-text" not in body


def test_headings_move_by_the_offset_asked():
    body = body_of(parse_markdown_to_mjml("## Section\n\n### Part", heading_offset=-1))
    print(body)
    assert "<h1>" in body and "<h2>" in body and "<h3>" not in body


def test_a_title_of_spaces_alone_says_nothing_under_the_image():
    body = body_of(parse_markdown_to_mjml('![The stand](https://x.com/s.jpg "   ")'))
    assert "mj-text" not in body
