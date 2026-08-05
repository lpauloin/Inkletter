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
