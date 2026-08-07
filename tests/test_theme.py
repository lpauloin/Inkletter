import pytest

from inkletter.colors import Blue, Slate, WHITE
from inkletter.exceptions import ThemeError
from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.theme import LEVELS, THEMES, Heading, Headings, Links, Text, Theme


def test_default_theme_is_complete():
    theme = Theme()
    assert theme.layout.width == "600px"
    assert theme.text.font_size == "14px"
    assert theme.links.underline is True
    assert theme.headings.color is None  # inherits text color


def test_theme_by_class():
    theme = Theme(
        text=Text(font_family="Georgia, serif"),
        links=Links(color=Blue.DARK, underline=False),
    )
    assert theme.text.font_family == "Georgia, serif"
    assert theme.links.color == Blue.DARK
    # untouched groups keep their defaults
    assert theme.layout.width == "600px"


def test_from_dict_partial_override():
    theme = Theme.from_dict(
        {
            "layout": {"width": "640px"},
            "links": {"color": "#c0392b", "underline": False},
        }
    )
    assert theme.layout.width == "640px"
    assert theme.layout.background_color == Theme().layout.background_color
    assert theme.links.color == "#c0392b"
    assert theme.links.underline is False


def test_from_dict_unknown_section():
    with pytest.raises(ThemeError, match=r"unknown section '\[colours\]'"):
        Theme.from_dict({"colours": {}})


def test_from_dict_unknown_key():
    with pytest.raises(ThemeError, match=r"unknown key 'colour' in \[links\]"):
        Theme.from_dict({"links": {"colour": "#fff"}})
    # the error lists the valid keys
    with pytest.raises(ThemeError, match="color, underline"):
        Theme.from_dict({"links": {"colour": "#fff"}})


def test_from_dict_bad_type():
    with pytest.raises(ThemeError, match=r"'underline' in \[links\] must be a bool"):
        Theme.from_dict({"links": {"underline": "yes"}})
    with pytest.raises(ThemeError, match=r"'width' in \[layout\] must be a str"):
        Theme.from_dict({"layout": {"width": 640}})


def test_round_trip_to_dict_from_dict():
    theme = Theme.from_dict({"text": {"color": "#222222"}})
    assert Theme.from_dict(theme.to_dict()) == theme


def test_from_toml(tmp_path):
    toml = tmp_path / "theme.toml"
    toml.write_text(
        """
[layout]
width = "640px"

[links]
underline = false
""",
        encoding="utf-8",
    )
    theme = Theme.from_toml(toml)
    assert theme.layout.width == "640px"
    assert theme.links.underline is False


def test_from_toml_missing_file(tmp_path):
    with pytest.raises(ThemeError, match="not found"):
        Theme.from_toml(tmp_path / "nope.toml")


def test_from_toml_invalid_toml(tmp_path):
    toml = tmp_path / "broken.toml"
    toml.write_text("[layout\nwidth=", encoding="utf-8")
    with pytest.raises(ThemeError, match="invalid TOML"):
        Theme.from_toml(toml)


def test_named_presets():
    assert Theme.named("default") == Theme()
    dark = Theme.named("dark")
    assert dark.layout.background_color == Slate.DARKEST
    assert dark.headings.color == WHITE


def test_named_unknown_lists_presets():
    with pytest.raises(ThemeError, match="available themes: .*dark"):
        Theme.named("nope")


@pytest.mark.parametrize("name", sorted(THEMES))
def test_all_presets_are_valid_themes(name):
    theme = THEMES[name]
    assert isinstance(theme, Theme)
    # every preset survives a to_dict/from_dict round-trip
    assert Theme.from_dict(theme.to_dict()) == theme


def test_table_section():
    theme = Theme.from_dict(
        {"table": {"border_color": "#123456", "header_background_color": "#eeeeee"}}
    )
    assert theme.table.border_color == "#123456"
    assert theme.table.header_background_color == "#eeeeee"
    assert theme.table.cell_padding == "8px 12px"


def test_table_unknown_key():
    with pytest.raises(ThemeError, match=r"unknown key 'borders' in \[table\]"):
        Theme.from_dict({"table": {"borders": "#fff"}})


# --- Web fonts ---

LORA = "https://fonts.googleapis.com/css2?family=Lora"
SERIF_STACK = "Lora, Georgia, serif"


def test_fonts_default_to_none_declared():
    assert Theme().fonts == ()


def test_fonts_from_dict():
    theme = Theme.from_dict({"text": {"font_family": SERIF_STACK}, "fonts": {"Lora": LORA}})
    assert theme.fonts == (("Lora", LORA),)


def test_several_fonts_keep_their_declared_order():
    inter = "https://fonts.example/inter.css"
    theme = Theme.from_dict(
        {
            "text": {"font_family": "Lora, Inter, serif"},
            "fonts": {"Lora": LORA, "Inter": inter},
        }
    )
    assert theme.fonts == (("Lora", LORA), ("Inter", inter))


def test_font_name_matching_ignores_case_and_quotes():
    theme = Theme(text=Text(font_family="'lora', Georgia"), fonts={"Lora": LORA})
    assert theme.fonts == (("Lora", LORA),)


def test_font_must_be_used_by_the_text_font_family():
    # MJML only loads a font used in a component attribute, and
    # text.font_family is the only theme setting that reaches one
    with pytest.raises(ThemeError, match="missing from text.font_family"):
        Theme(text=Text(font_family="Georgia, serif"), fonts={"Lora": LORA})


def test_font_declared_for_headings_alone_is_refused():
    with pytest.raises(ThemeError, match="rely on the fallback"):
        Theme.from_dict({"headings": {"font_family": SERIF_STACK}, "fonts": {"Lora": LORA}})


def test_font_url_must_be_http():
    with pytest.raises(ThemeError, match="http:// or https://"):
        Theme(text=Text(font_family=SERIF_STACK), fonts={"Lora": "/local/lora.css"})


def test_font_url_must_be_a_string():
    with pytest.raises(ThemeError, match="must be a URL string"):
        Theme(text=Text(font_family=SERIF_STACK), fonts={"Lora": 3})


def test_font_name_cannot_be_empty():
    with pytest.raises(ThemeError, match="cannot be empty"):
        Theme(text=Text(font_family=SERIF_STACK), fonts={"  ": LORA})


def test_theme_with_fonts_stays_hashable_and_round_trips():
    theme = Theme(text=Text(font_family=SERIF_STACK), fonts={"Lora": LORA})
    assert hash(theme) == hash(Theme(text=Text(font_family=SERIF_STACK), fonts={"Lora": LORA}))
    assert Theme.from_dict(theme.to_dict()) == theme


def test_font_url_with_query_parameters():
    # the shape a real Google Fonts URL takes
    swap = "https://fonts.googleapis.com/css2?family=Lora&display=swap"
    theme = Theme(text=Text(font_family=SERIF_STACK), fonts={"Lora": swap})
    assert theme.fonts == (("Lora", swap),)


def test_two_word_font_name_matches_a_quoted_stack():
    url = "https://fonts.example/pt.css"
    for stack in ['"PT Serif", Georgia', "'PT Serif', Georgia", "PT Serif, Georgia"]:
        theme = Theme(text=Text(font_family=stack), fonts={"PT Serif": url})
        assert theme.fonts == (("PT Serif", url),)


def test_font_declared_twice_is_refused():
    with pytest.raises(ThemeError, match="declared twice"):
        Theme(text=Text(font_family=SERIF_STACK), fonts=(("Lora", LORA), ("lora", LORA)))


def test_fonts_from_toml(tmp_path):
    path = tmp_path / "theme.toml"
    path.write_text(
        f'[text]\nfont_family = "{SERIF_STACK}"\n\n[fonts]\nLora = "{LORA}"\n',
        encoding="utf-8",
    )
    assert Theme.from_toml(path).fonts == (("Lora", LORA),)


def test_empty_fonts_section():
    assert Theme.from_dict({"fonts": {}}).fonts == ()


def test_fonts_must_be_pairs():
    with pytest.raises(ThemeError, match="map a font name to a URL"):
        Theme(text=Text(font_family=SERIF_STACK), fonts=(("Lora",),))


def test_presets_declare_no_web_font():
    # the rendering must not depend on a CDN by default
    assert all(theme.fonts == () for theme in THEMES.values())


# --- Heading levels ---
#
# One object per level, holding what belongs to that level. Alignment
# rides the mj-text attribute rather than the head CSS: that comes out
# as `td align` *and* as an inlined text-align, where an
# `h1 { text-align }` rule would depend on a <style> block some clients
# drop. Left is MJML's own default, so nothing is emitted for it.


def test_every_level_has_a_size_and_an_alignment():
    headings = Theme().headings
    assert [headings.at(n).size for n in LEVELS] == [
        "28px",
        "22px",
        "18px",
        "16px",
        "14px",
        "13px",
    ]
    assert {headings.at(n).align for n in LEVELS} == {"left"}


def test_every_level_is_sized_in_the_css():
    css = Theme().to_css()
    print(css)
    for number in LEVELS:
        assert f"h{number} {{ font-size:" in css


def test_the_default_emits_no_alignment_at_all():
    # an unchanged theme must render byte for byte as before
    source = "# Titre\n\nTexte."
    assert parse_markdown_to_mjml(source) == parse_markdown_to_mjml(
        source, theme=Theme(headings=Headings(h1=Heading(size="28px", align="left")))
    )


@pytest.mark.parametrize("level", [1, 2, 3])
@pytest.mark.parametrize("align", ["center", "right"])
def test_each_level_carries_its_own_alignment(level, align):
    theme = Theme(headings=Headings(**{f"h{level}": Heading(size="20px", align=align)}))
    actual = parse_markdown_to_mjml(f"{'#' * level} Titre\n\nTexte.", theme=theme)
    print(actual)
    assert f'<mj-text align="{align}">\n          <h{level}>' in actual


def test_the_other_levels_stay_put():
    # the reason for one object per level: a centred h1 over
    # left-aligned h2s is what a newsletter actually looks like
    theme = Theme(headings=Headings(h1=Heading(size="28px", align="center")))
    actual = parse_markdown_to_mjml("# Un\n\n## Deux\n\n### Trois", theme=theme)
    print(actual)
    # in the body only: the head declares align="center" for images and
    # buttons by default, and counting the whole document would measure
    # those instead
    body = actual[actual.index("<mj-body") :]
    assert body.count('align="center"') == 1


def test_it_reaches_both_paths_in_the_compiled_html():
    # the reason for the attribute: Outlook honours the td, everything
    # else honours the inlined style, and neither needs the head
    from inkletter.md_to_html import parse_markdown_to_html

    theme = Theme(headings=Headings(h1=Heading(size="28px", align="center")))
    html = parse_markdown_to_html("# Titre\n\nTexte.", theme=theme)
    print(html)
    assert '<td align="center"' in html
    assert "text-align:center;" in html


@pytest.mark.parametrize("value", ["justify", "middle", "LEFT", ""])
def test_an_alignment_that_is_not_one_is_refused(value):
    with pytest.raises(ThemeError) as error:
        Theme(headings=Headings(h2=Heading(size="22px", align=value)))
    assert str(error.value) == (
        f"align '{value}' in [headings.h2] is not an alignment; use left, center, right"
    )


# --- The nested section in a theme file ---


def test_a_level_is_its_own_toml_section():
    theme = Theme.from_dict({"headings": {"h1": {"size": "32px", "align": "center"}}})
    assert theme.headings.at(1) == Heading(size="32px", align="center")


def test_a_partial_level_keeps_the_rest_of_its_defaults():
    # [headings.h1] align = "center" must not have to repeat the size
    theme = Theme.from_dict({"headings": {"h1": {"align": "center"}}})
    assert theme.headings.at(1) == Heading(size="28px", align="center")
    assert theme.headings.at(2) == Heading(size="22px", align="left")


def test_a_level_sits_beside_the_flat_keys():
    theme = Theme.from_dict({"headings": {"font_weight": "600", "h1": {"align": "right"}}})
    assert theme.headings.font_weight == "600"
    assert theme.headings.at(1).align == "right"


def test_it_survives_a_round_trip_through_toml():
    theme = Theme.from_dict({"headings": {"h1": {"align": "center"}}})
    assert Theme.from_dict(theme.to_dict()) == theme


@pytest.mark.parametrize(
    "data, message",
    [
        ({"h7": {}}, "unknown key 'h7' in [headings]"),
        ({"h1": {"taille": "2px"}}, "unknown key 'taille' in [headings.h1]"),
        ({"h1": {"size": 12}}, "key 'size' in [headings.h1] must be a str"),
    ],
)
def test_a_mistake_in_a_level_is_refused(data, message):
    with pytest.raises(ThemeError) as error:
        Theme.from_dict({"headings": data})
    assert message in str(error.value)


# --- The other two sections that carry an alignment ---
#
# They feed the same mj-* align attribute, and until now neither was
# checked: a typo showed up as an element quietly not moving.


@pytest.mark.parametrize("section", ["buttons", "images"])
@pytest.mark.parametrize("value", ["justify", "middle", "LEFT"])
def test_every_alignment_in_the_theme_is_checked(section, value):
    with pytest.raises(ThemeError) as error:
        Theme.from_dict({section: {"align": value}})
    assert str(error.value) == (
        f"align '{value}' in [{section}] is not an alignment; use left, center, right"
    )


def test_the_defaults_they_ship_with_are_valid():
    assert Theme().buttons.align == "center"
    assert Theme().images.align == "center"
