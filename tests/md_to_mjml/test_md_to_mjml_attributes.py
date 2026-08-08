"""What an attributed image emits, in every context it can land in."""

import pytest

from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body
from inkletter.md_to_text import parse_markdown_to_text


def test_width_becomes_an_mj_image_attribute():
    actual = parse_markdown_to_mjml("![Acme](https://x.com/l.png){width=96px}")
    print(actual)
    expected = wrap_mjml_body('<mj-image src="https://x.com/l.png" alt="Acme" width="96px"/>')
    assert actual == expected


def test_a_bare_number_is_pixels():
    actual = parse_markdown_to_mjml("![Acme](https://x.com/l.png){width=96}")
    print(actual)
    assert 'width="96px"' in actual


def test_the_three_together():
    actual = parse_markdown_to_mjml(
        "![Acme](https://x.com/l.png){width=96px height=40px align=left}"
    )
    print(actual)
    expected = wrap_mjml_body(
        '<mj-image src="https://x.com/l.png" alt="Acme"'
        ' width="96px" height="40px" align="left"/>'
    )
    assert actual == expected


def test_a_linked_image_keeps_its_width():
    actual = parse_markdown_to_mjml("[![Acme](https://x.com/l.png)](https://x.com){width=320px}")
    print(actual)
    expected = wrap_mjml_body(
        '<mj-image src="https://x.com/l.png" href="https://x.com" alt="Acme" width="320px"/>'
    )
    assert actual == expected


def test_an_image_in_a_row_keeps_both_its_padding_and_its_width():
    # the row spacing comes from the theme, the width from the author:
    # neither may erase the other
    actual = parse_markdown_to_mjml(
        "![a](https://x.com/a.png){width=40px} ![b](https://x.com/b.png)"
    )
    print(actual)
    assert 'alt="a" padding="10px 8px" width="40px"' in actual
    assert 'alt="b" padding="10px 8px"/>' in actual


def test_an_image_in_a_media_object_keeps_its_width():
    actual = parse_markdown_to_mjml(
        "![a](https://x.com/a.png){width=40px} and some text beside it."
    )
    print(actual)
    assert 'alt="a" width="40px"' in actual


def test_a_manual_image_carries_its_size_in_the_style():
    # inside an mj-text (here a heading) an mj-image would leak, so the
    # image is a plain <img> and its facts go into the style it already has
    actual = parse_markdown_to_mjml("# Title ![i](https://x.com/i.png){width=24px}")
    print(actual)
    assert 'style="max-width: 100%; height: auto; width: 24px;"' in actual


def test_a_manual_image_ignores_alignment():
    # an image in a run of text sits where the text puts it
    actual = parse_markdown_to_mjml("# Title ![i](https://x.com/i.png){align=left}")
    print(actual)
    assert "align" not in actual.split("<mj-body")[1]


def test_the_width_reaches_the_compiled_html():
    # mjml2html splits it: the cell gets the CSS width, the img the
    # HTML attribute Outlook needs
    html = parse_markdown_to_html("![Acme](https://x.com/l.png){width=96px}")
    print(html)
    assert "{width=96px}" not in html
    assert "width:96px;" in html
    assert 'width="96"' in html


def test_a_width_holds_on_mobile():
    """fluid-on-mobile goes full width *even though a width is set*, so the
    old head default undid, on a phone, the one thing the author asked for.
    An image without a width follows its column either way."""
    assert "fluid-on-mobile" not in parse_markdown_to_mjml(
        "![Acme](https://x.com/l.png){width=96px}"
    )
    html = parse_markdown_to_html("![Acme](https://x.com/l.png){width=96px}")
    # the rule always sits in the head <style>; what matters is that no
    # element carries the class that would trigger it
    assert 'class="mj-full-width-mobile"' not in html


def test_images_stay_fluid_without_the_attribute_syntax():
    """With --no-link-attributes no image can carry a width, so the default
    is kept and such a document renders exactly as it did before."""
    actual = parse_markdown_to_mjml("![Acme](https://x.com/l.png)", link_attributes=False)
    print(actual)
    assert '<mj-image align="center" fluid-on-mobile="true"/>' in actual


# --- The text half ---


ATTRIBUTED = [
    "![Acme](https://x.com/l.png){width=96px}",
    "[![Acme](https://x.com/l.png)](https://x.com){width=320px}",
    "![a](https://x.com/a.png){width=40px} ![b](https://x.com/b.png){height=20px}",
    "![a](https://x.com/a.png){align=left} and some text beside it.",
    "# Title ![i](https://x.com/i.png){width=24px}",
]


@pytest.mark.parametrize("markdown", ATTRIBUTED)
def test_the_text_output_is_the_document_without_its_braces(markdown):
    # attributes are dropped whole: TextCodegen never reads them, so the
    # plain-text half is exactly what it would be without the blocks
    import re

    bare = re.sub(r"\{[^}]*\}", "", markdown)
    print(parse_markdown_to_text(markdown))
    assert parse_markdown_to_text(markdown) == parse_markdown_to_text(bare)


@pytest.mark.parametrize("markdown", ATTRIBUTED)
def test_no_brace_survives_into_the_text(markdown):
    assert "{" not in parse_markdown_to_text(markdown)
