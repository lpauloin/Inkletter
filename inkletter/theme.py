"""Themes: the look of the generated email.

A theme is a value: frozen dataclasses grouped by concern, every field
with a sensible default. Build one directly (`Theme(text=Text(...))`),
from a dict (`Theme.from_dict`), from a partial TOML file
(`Theme.from_toml`) or pick a preset (`Theme.named("night")`) — all
paths produce the same kind of object.
"""

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from inkletter.colors import WHITE, Blue, Gray, Green, Red, Slate, Yellow


class ThemeError(Exception):
    """Invalid theme definition (unknown key, bad type, unknown preset)."""


@dataclass(frozen=True)
class Layout:
    width: str = "600px"
    background_color: str = Gray.LIGHTEST
    content_background_color: str = WHITE
    section_padding: str = "0"


@dataclass(frozen=True)
class Text:
    font_family: str = "Helvetica, Arial, sans-serif"
    font_size: str = "14px"
    line_height: str = "1.6"
    color: str = Gray.DARK


@dataclass(frozen=True)
class Headings:
    font_family: str | None = None  # None inherits Text.font_family
    color: str | None = None  # None inherits Text.color
    font_weight: str = "700"
    h1_size: str = "28px"
    h2_size: str = "22px"
    h3_size: str = "18px"


@dataclass(frozen=True)
class Links:
    color: str = Blue.DARK
    underline: bool = True


@dataclass(frozen=True)
class Code:
    font_family: str = "Menlo, Consolas, monospace"
    background_color: str = Gray.LIGHTEST
    color: str = Gray.DARKEST


@dataclass(frozen=True)
class Quote:
    color: str = Gray.BASE
    border_color: str = Gray.LIGHT
    font_style: str = "italic"


@dataclass(frozen=True)
class Divider:
    color: str = Gray.LIGHT
    width: str = "1px"


@dataclass(frozen=True)
class Theme:
    layout: Layout = field(default_factory=Layout)
    text: Text = field(default_factory=Text)
    headings: Headings = field(default_factory=Headings)
    links: Links = field(default_factory=Links)
    code: Code = field(default_factory=Code)
    quote: Quote = field(default_factory=Quote)
    divider: Divider = field(default_factory=Divider)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ThemeError("a theme must be a mapping of sections")
        groups = {f.name: f.default_factory for f in fields(cls)}
        kwargs = {}
        for group_name, group_data in data.items():
            if group_name not in groups:
                raise ThemeError(
                    f"unknown section '[{group_name}]'; "
                    f"valid sections: {', '.join(sorted(groups))}"
                )
            kwargs[group_name] = _build_group(groups[group_name], group_name, group_data)
        return cls(**kwargs)

    @classmethod
    def from_toml(cls, path):
        path = Path(path)
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError:
            raise ThemeError(f"theme file not found: {path}")
        except tomllib.TOMLDecodeError as e:
            raise ThemeError(f"invalid TOML in {path}: {e}")
        return cls.from_dict(data)

    @classmethod
    def named(cls, name):
        try:
            return THEMES[name]
        except KeyError:
            raise ThemeError(
                f"unknown theme '{name}'; "
                f"available themes: {', '.join(sorted(THEMES))}"
            )

    def to_dict(self):
        return asdict(self)


def _build_group(group_cls, group_name, group_data):
    if not isinstance(group_data, dict):
        raise ThemeError(f"section '[{group_name}]' must be a mapping")
    group_fields = {f.name: f for f in fields(group_cls)}
    for key, value in group_data.items():
        if key not in group_fields:
            raise ThemeError(
                f"unknown key '{key}' in [{group_name}]; "
                f"valid keys: {', '.join(sorted(group_fields))}"
            )
        default = group_fields[key].default
        if isinstance(default, bool):
            if not isinstance(value, bool):
                raise ThemeError(f"key '{key}' in [{group_name}] must be a bool")
        elif not isinstance(value, str) and not (default is None and value is None):
            raise ThemeError(f"key '{key}' in [{group_name}] must be a str")
    return group_cls(**group_data)


# --- Presets ---


def _hue_theme(hue):
    return Theme(
        layout=Layout(background_color=hue.LIGHTEST),
        headings=Headings(color=hue.DARKEST),
        links=Links(color=hue.DARK),
        quote=Quote(color=Gray.BASE, border_color=hue.LIGHT),
        divider=Divider(color=hue.LIGHT),
        code=Code(background_color=hue.LIGHTEST, color=hue.DARKEST),
    )


_NIGHT = Theme(
    layout=Layout(
        background_color=Slate.DARKEST,
        content_background_color=Slate.DARK,
    ),
    text=Text(color=Slate.LIGHT),
    headings=Headings(color=WHITE),
    links=Links(color=Blue.LIGHT),
    code=Code(background_color=Slate.DARKEST, color=Slate.LIGHT),
    quote=Quote(color=Slate.BASE, border_color=Slate.BASE),
    divider=Divider(color=Slate.BASE),
)

THEMES = {
    "default": Theme(),
    "night": _NIGHT,
    "dark": _NIGHT,
    "crystal": Theme(
        layout=Layout(background_color=Slate.LIGHTEST),
        text=Text(color=Slate.DARK),
        headings=Headings(color=Slate.DARKEST),
        links=Links(color=Blue.BASE),
        quote=Quote(color=Slate.BASE, border_color=Blue.LIGHT),
        divider=Divider(color=Slate.LIGHT),
        code=Code(background_color=Slate.LIGHTEST, color=Slate.DARKEST),
    ),
    "blue": _hue_theme(Blue),
    "green": _hue_theme(Green),
    "red": _hue_theme(Red),
    "yellow": _hue_theme(Yellow),
}
