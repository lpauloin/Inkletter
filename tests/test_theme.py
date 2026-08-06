import pytest

from inkletter.colors import Blue, Slate, WHITE
from inkletter.theme import THEMES, Links, Text, Theme, ThemeError


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
    theme = Theme.from_dict(
        {"text": {"font_family": SERIF_STACK}, "fonts": {"Lora": LORA}}
    )
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
        Theme.from_dict(
            {"headings": {"font_family": SERIF_STACK}, "fonts": {"Lora": LORA}}
        )


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
    assert hash(theme) == hash(
        Theme(text=Text(font_family=SERIF_STACK), fonts={"Lora": LORA})
    )
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
        Theme(
            text=Text(font_family=SERIF_STACK), fonts=(("Lora", LORA), ("lora", LORA))
        )


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
