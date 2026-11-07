import pytest

from inkletter.exceptions import MarkupError
from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment
from inkletter.shortener import URLFactory

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


# Asked for, the pictures are drawn: a page that serves the addresses itself —
# a document printed to a PDF, pasted into an editor.


def test_asked_for_an_image_alone_is_a_figure_its_title_the_caption():
    actual = parse_markdown_to_html_fragment(
        '![The stand](https://x.com/s.jpg "Thursday morning")', images=True
    )
    print(actual)
    assert (
        actual
        == '<figure><img src="https://x.com/s.jpg" alt="The stand"><figcaption>Thursday morning</figcaption></figure>'
    )


def test_asked_for_an_image_without_title_has_no_caption():
    actual = parse_markdown_to_html_fragment("![The stand](https://x.com/s.jpg)", images=True)
    print(actual)
    assert actual == '<figure><img src="https://x.com/s.jpg" alt="The stand"></figure>'


def test_asked_for_an_image_within_a_line_stays_in_it():
    actual = parse_markdown_to_html_fragment("Before ![a](https://x.com/a.png) after", images=True)
    print(actual)
    assert actual == '<p>Before <img src="https://x.com/a.png" alt="a"> after</p>'


def test_asked_for_images_side_by_side_share_a_paragraph():
    actual = parse_markdown_to_html_fragment(
        "![A](https://x.com/a.png) ![B](https://x.com/b.png)", images=True
    )
    print(actual)
    assert (
        actual
        == '<p><img src="https://x.com/a.png" alt="A"> <img src="https://x.com/b.png" alt="B"></p>'
    )


def test_asked_for_an_image_that_is_no_web_address_stays_its_text():
    actual = parse_markdown_to_html_fragment("![Secret](file:///etc/passwd)", images=True)
    print(actual)
    assert actual == "<p>Secret</p>"


class InThePage(URLFactory):
    """Carries each picture inside the page, as a printed page does."""

    def rewrite_image(self, url):
        return "data:image/png;base64,AAAA"


def test_asked_for_a_picture_carried_inside_the_page_is_drawn():
    actual = parse_markdown_to_html_fragment(
        '![Plan](vis_1 "Lundi")', images=True, url_factory=InThePage()
    )
    print(actual)
    assert actual == (
        '<figure><img src="data:image/png;base64,AAAA" alt="Plan"><figcaption>Lundi</figcaption></figure>'
    )


def test_asked_for_a_data_address_that_is_no_picture_stays_its_text():
    actual = parse_markdown_to_html_fragment("![Page](data:text/html;base64,PHA+)", images=True)
    print(actual)
    assert "<img" not in actual


def test_asked_for_an_image_escapes_its_address_and_its_text():
    actual = parse_markdown_to_html_fragment(
        '![a "b" & c](https://x.com/i.png?a=1&b=2)', images=True
    )
    print(actual)
    assert (
        actual
        == '<figure><img src="https://x.com/i.png?a=1&amp;b=2" alt="a &quot;b&quot; &amp; c"></figure>'
    )


def test_asked_for_a_row_mixing_a_linked_image_draws_both():
    actual = parse_markdown_to_html_fragment(
        "![A](https://x.com/a.png) [![B](https://x.com/b.png)](https://example.com)", images=True
    )
    print(actual)
    assert (
        actual
        == '<p><img src="https://x.com/a.png" alt="A"> <a href="https://example.com"><img src="https://x.com/b.png" alt="B"></a></p>'
    )


def test_asked_for_a_row_mixing_drawn_and_undrawn_images_keeps_them_apart():
    actual = parse_markdown_to_html_fragment(
        "![A](https://x.com/a.png) ![Plan](plan.png) ![](other.png) ![C](https://x.com/c.png)",
        images=True,
    )
    print(actual)
    assert actual == (
        '<p><img src="https://x.com/a.png" alt="A"> Plan <img src="https://x.com/c.png" alt="C"></p>'
    )


def test_asked_for_a_title_of_spaces_alone_writes_no_caption():
    actual = parse_markdown_to_html_fragment('![Plan](https://x.com/p.png "   ")', images=True)
    print(actual)
    assert actual == '<figure><img src="https://x.com/p.png" alt="Plan"></figure>'


def test_asked_for_a_linked_image_beside_its_text_keeps_its_figure():
    actual = parse_markdown_to_html_fragment(
        '[![Plan](https://x.com/p.png "Lundi"){size=small}](https://example.com) The plan.',
        images=True,
    )
    print(actual)
    assert actual == (
        '<figure data-size="small"><a href="https://example.com">'
        '<img src="https://x.com/p.png" alt="Plan"></a><figcaption>Lundi</figcaption></figure>'
        "<p>The plan.</p>"
    )


def test_asked_for_a_picture_inside_the_page_is_drawn_only_in_a_format_the_tree_accepts():
    actual = parse_markdown_to_html_fragment(
        "![Plan](data:image/svg+xml;base64,PHN2Zz4=)", images=True
    )
    print(actual)
    assert "<img" not in actual


def test_asked_for_an_image_laid_small_says_so_on_its_figure():
    actual = parse_markdown_to_html_fragment(
        '![The stand](https://x.com/s.jpg "Thursday"){size=small}', images=True
    )
    print(actual)
    assert (
        actual
        == '<figure data-size="small"><img src="https://x.com/s.jpg" alt="The stand"><figcaption>Thursday</figcaption></figure>'
    )


def test_an_image_laid_full_is_the_plain_figure():
    actual = parse_markdown_to_html_fragment(
        "![The stand](https://x.com/s.jpg){size=full}", images=True
    )
    print(actual)
    assert actual == '<figure><img src="https://x.com/s.jpg" alt="The stand"></figure>'


def test_a_size_that_is_no_size_is_refused():
    with pytest.raises(MarkupError, match="'size=huge' is not a size"):
        parse_markdown_to_html_fragment("![a](https://x.com/s.jpg){size=huge}", images=True)
