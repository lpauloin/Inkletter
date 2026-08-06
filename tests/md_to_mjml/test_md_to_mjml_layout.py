import pytest

from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.theme import Images, Theme, ThemeError, split_media_ratio

# --- Image rows ---


def test_image_row_two_columns():
    actual = parse_markdown_to_mjml(
        "![a](https://x.com/a.png) ![b](https://x.com/b.png)"
    )
    print(actual)
    expected = """\
<mjml>
  <mj-body>
    <mj-section>
      <mj-column>
        <mj-image src="https://x.com/a.png" alt="a" padding="10px 8px"/>
      </mj-column>
      <mj-column>
        <mj-image src="https://x.com/b.png" alt="b" padding="10px 8px"/>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""
    assert actual == expected


def test_image_row_between_paragraphs_keeps_flow_bands():
    markdown = "Avant.\n\n![a](https://x.com/a.png) ![b](https://x.com/b.png)\n\nAprès."
    actual = parse_markdown_to_mjml(markdown)
    print(actual)
    assert actual.count("<mj-section>") == 3
    # flow bands are single-column
    assert actual.count("<mj-column>") == 4


def test_five_images_wrap_in_rows_of_three():
    markdown = " ".join(f"![i{n}](https://x.com/{n}.png)" for n in range(5))
    actual = parse_markdown_to_mjml(markdown)
    print(actual)
    assert actual.count("<mj-section>") == 2
    assert actual.count("<mj-image") == 5


def test_four_images_stay_on_one_row():
    markdown = " ".join(f"![i{n}](https://x.com/{n}.png)" for n in range(4))
    actual = parse_markdown_to_mjml(markdown)
    assert actual.count("<mj-section>") == 1
    assert actual.count("<mj-column>") == 4


def test_row_gap_comes_from_the_theme():
    theme = Theme(images=Images(row_gap="2px"))
    actual = parse_markdown_to_mjml(
        "![a](https://x.com/a.png) ![b](https://x.com/b.png)", theme=theme
    )
    assert 'padding="10px 2px"' in actual


# --- Media objects ---


def test_media_object_left():
    actual = parse_markdown_to_mjml(
        "![Jean](https://x.com/j.png) Jean rejoint l'équipe."
    )
    print(actual)
    expected = """\
<mjml>
  <mj-body>
    <mj-section>
      <mj-column width="30%">
        <mj-image src="https://x.com/j.png" alt="Jean"/>
      </mj-column>
      <mj-column width="70%">
        <mj-text>
          Jean rejoint l'équipe.
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""
    assert actual == expected


def test_media_object_right_uses_rtl_with_image_first_in_dom():
    actual = parse_markdown_to_mjml(
        "Jean rejoint l'équipe. ![Jean](https://x.com/j.png)"
    )
    print(actual)
    assert '<mj-section direction="rtl">' in actual
    # DOM order: image column before text column, so mobile stacks image on top
    assert actual.index("mj-image") < actual.index("mj-text")


def test_media_ratio_comes_from_the_theme():
    theme = Theme(images=Images(media_ratio="40%"))
    actual = parse_markdown_to_mjml(
        "![J](https://x.com/j.png) Texte à côté.", theme=theme
    )
    assert '<mj-column width="40%">' in actual
    assert '<mj-column width="60%">' in actual


def test_stacked_layout_keeps_image_then_text():
    theme = Theme(images=Images(text_layout="stacked"))
    actual = parse_markdown_to_mjml(
        "![J](https://x.com/j.png) Texte en dessous.", theme=theme
    )
    print(actual)
    assert "direction" not in actual
    assert 'width="30%"' not in actual
    assert actual.index("mj-image") < actual.index("Texte en dessous")


# --- Theme [images] ---


def test_images_section_unknown_key():
    with pytest.raises(ThemeError, match=r"unknown key 'gap' in \[images\]"):
        Theme.from_dict({"images": {"gap": "4px"}})


def test_border_radius_reaches_head_and_manual_images():
    theme = Theme(images=Images(border_radius="6px"))
    actual = parse_markdown_to_mjml("- ![i](https://x.com/i.png) item", theme=theme)
    assert 'border-radius="6px"' in actual  # mj-image default in head
    assert "border-radius: 6px;" in actual  # manual <img> in the list


@pytest.mark.parametrize(
    "ratio, expected", [("30%", ("30%", "70%")), ("25", ("25%", "75%"))]
)
def test_split_media_ratio(ratio, expected):
    assert split_media_ratio(ratio) == expected


@pytest.mark.parametrize("ratio", ["0%", "100%", "abc", ""])
def test_split_media_ratio_invalid(ratio):
    with pytest.raises(ThemeError, match="media_ratio"):
        split_media_ratio(ratio)


# --- End to end ---


def test_final_html_renders_row_and_media_columns():
    markdown = (
        "![a](https://x.com/a.png) ![b](https://x.com/b.png)\n\n"
        "![J](https://x.com/j.png) Jean rejoint l'équipe."
    )
    html = parse_markdown_to_html(markdown, theme=Theme())
    # MJML emitted real columns with the mobile stacking machinery
    assert "mj-column-per-50" in html  # the row of two
    assert "mj-column-per-30" in html
    assert "mj-column-per-70" in html
    assert "@media" in html
