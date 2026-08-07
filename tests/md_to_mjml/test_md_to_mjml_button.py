import pytest

from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import (
    parse_markdown_to_mjml,
    wrap_mjml_body,
    wrap_mjml_document,
)
from inkletter.exceptions import ThemeError
from inkletter.theme import Buttons, Theme

URL = "https://exemple.com/go"


def head_button_line(mjml):
    """The full mj-button defaults line from the head mj-attributes."""
    return next(
        line.strip() for line in mjml.splitlines() if "mj-button" in line and "background" in line
    )


# --- In the flow band ---


def test_button_snapshot():
    actual = parse_markdown_to_mjml(f"**[Get started]({URL})**")
    print(actual)
    expected = wrap_mjml_body(f'<mj-button href="{URL}">Get started</mj-button>')
    assert actual == expected


def test_button_stays_in_the_flow_band():
    actual = parse_markdown_to_mjml(f"Avant.\n\n**[Go]({URL})**\n\nAprès.")
    print(actual)
    expected = wrap_mjml_body(f"""\
<mj-text>
  Avant.
</mj-text>
<mj-button href="{URL}">Go</mj-button>
<mj-text>
  Après.
</mj-text>""")
    assert actual == expected


def test_button_between_image_row_and_media_object():
    markdown = (
        "![a](https://x.com/a.png) ![b](https://x.com/b.png)\n\n"
        f"**[Go]({URL})**\n\n"
        "![J](https://x.com/j.png) Un média-objet."
    )
    actual = parse_markdown_to_mjml(markdown)
    print(actual)
    expected = wrap_mjml_document(f"""\
<mj-section>
  <mj-column>
    <mj-image src="https://x.com/a.png" alt="a" padding="10px 8px"/>
  </mj-column>
  <mj-column>
    <mj-image src="https://x.com/b.png" alt="b" padding="10px 8px"/>
  </mj-column>
</mj-section>
<mj-section>
  <mj-column>
    <mj-button href="{URL}">Go</mj-button>
  </mj-column>
</mj-section>
<mj-section>
  <mj-column width="30%">
    <mj-image src="https://x.com/j.png" alt="J"/>
  </mj-column>
  <mj-column width="70%">
    <mj-text>
      Un média-objet.
    </mj-text>
  </mj-column>
</mj-section>""")
    assert actual == expected


# --- Label content (is_in_button) ---


def test_label_with_emphasis_and_code():
    actual = parse_markdown_to_mjml(f"**[*Vite* `go` !]({URL})**")
    print(actual)
    expected = wrap_mjml_body(
        f'<mj-button href="{URL}"><em>Vite</em> <code>go</code> !</mj-button>'
    )
    assert actual == expected


def test_label_is_escaped():
    actual = parse_markdown_to_mjml(f"**[A & B < C]({URL})**")
    print(actual)
    expected = wrap_mjml_body(f'<mj-button href="{URL}">A &amp; B &lt; C</mj-button>')
    assert actual == expected


def test_label_inline_html_passthrough():
    actual = parse_markdown_to_mjml(f"**[Go <span>!</span>]({URL})**")
    print(actual)
    expected = wrap_mjml_body(f'<mj-button href="{URL}">Go <span>!</span></mj-button>')
    assert actual == expected


def test_link_title_lands_on_the_button():
    actual = parse_markdown_to_mjml(f'**[Go]({URL} "Mon titre")**')
    print(actual)
    expected = wrap_mjml_body(f'<mj-button href="{URL}" title="Mon titre">Go</mj-button>')
    assert actual == expected


# --- Theme ---


def test_head_button_attributes_inherit_links_color():
    actual = parse_markdown_to_mjml(f"**[Go]({URL})**", theme=Theme())
    print(actual)
    assert head_button_line(actual) == (
        '<mj-button background-color="#1d4ed8" color="#ffffff"'
        ' border-radius="6px" font-weight="700" inner-padding="12px 24px"'
        ' align="center" font-family="Helvetica, Arial, sans-serif"'
        ' font-size="14px"/>'
    )


def test_dark_preset_defines_a_readable_button():
    actual = parse_markdown_to_mjml(f"**[Go]({URL})**", theme=Theme.named("dark"))
    print(actual)
    assert head_button_line(actual) == (
        '<mj-button background-color="#bfdbfe" color="#0f172a"'
        ' border-radius="6px" font-weight="700" inner-padding="12px 24px"'
        ' align="center" font-family="Helvetica, Arial, sans-serif"'
        ' font-size="14px"/>'
    )


def test_custom_buttons_theme():
    theme = Theme(buttons=Buttons(background_color="#c0392b", border_radius="0"))
    actual = parse_markdown_to_mjml(f"**[Go]({URL})**", theme=theme)
    print(actual)
    assert head_button_line(actual) == (
        '<mj-button background-color="#c0392b" color="#ffffff"'
        ' border-radius="0" font-weight="700" inner-padding="12px 24px"'
        ' align="center" font-family="Helvetica, Arial, sans-serif"'
        ' font-size="14px"/>'
    )


def test_buttons_section_unknown_key():
    with pytest.raises(ThemeError, match=r"unknown key 'colour' in \[buttons\]"):
        Theme.from_dict({"buttons": {"colour": "#fff"}})


# --- The conversion parameter ---


def test_bold_link_is_button_off_restores_previous_output():
    actual = parse_markdown_to_mjml(f"**[Go]({URL})**", bold_link_is_button=False)
    print(actual)
    expected = wrap_mjml_body(f"""\
<mj-text>
  <strong><a href="{URL}">Go</a></strong>
</mj-text>""")
    assert actual == expected


def test_bold_link_is_button_off_with_theme():
    actual = parse_markdown_to_mjml(f"**[Go]({URL})**", theme=Theme(), bold_link_is_button=False)
    print(actual)
    body = actual[actual.find("<mj-body") :]
    assert body == f"""\
<mj-body width="600px" background-color="#f9fafb">
    <mj-section>
      <mj-column>
        <mj-text>
          <strong><a href="{URL}">Go</a></strong>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""


# --- End to end (the final HTML is too large to snapshot) ---


def test_final_html_renders_the_button():
    html = parse_markdown_to_html(f"**[Get started]({URL})**", theme=Theme())
    assert 'role="presentation"' in html
    assert f'href="{URL}"' in html
    assert "Get started" in html
    # theme values are inlined
    assert "#1d4ed8" in html
    assert "border-radius:6px" in html.replace(" ", "")


def test_a_deeply_nested_image_still_forbids_the_button():
    # the image always wins, however deep it sits in the label — this is
    # what the scope records for the promotion to read
    actual = parse_markdown_to_mjml("**[*![alt](https://x.com/i.png)*](https://x.com)**")
    print(actual)
    assert "<mj-button" not in actual.split("<mj-body")[1]
    assert "<img" in actual or "mj-image" in actual
