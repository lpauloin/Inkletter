"""Themes: the look of the generated email.

A theme is a value: frozen dataclasses grouped by concern, every field
with a sensible default. Build one directly (`Theme(text=Text(...))`),
from a dict (`Theme.from_dict`), from a partial TOML file
(`Theme.from_toml`) or pick a preset (`Theme.named("dark")`) — all
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
    section_padding: str = "16px 0"


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
class Table:
    border_color: str = Gray.LIGHT  # horizontal row rules
    cell_padding: str = "8px 12px"
    header_color: str | None = None  # None inherits the text color
    header_background_color: str | None = None  # None means transparent


@dataclass(frozen=True)
class Theme:
    layout: Layout = field(default_factory=Layout)
    text: Text = field(default_factory=Text)
    headings: Headings = field(default_factory=Headings)
    links: Links = field(default_factory=Links)
    code: Code = field(default_factory=Code)
    quote: Quote = field(default_factory=Quote)
    divider: Divider = field(default_factory=Divider)
    table: Table = field(default_factory=Table)

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

    def to_css(self):
        """CSS rules for the raw HTML living inside mj-text blocks.

        Emitted in an <mj-style inline="inline"> so mjml2html inlines
        them into the tags, as required by most email clients.
        """
        heading_font = self.headings.font_family or self.text.font_family
        heading_color = self.headings.color or self.text.color
        decoration = "underline" if self.links.underline else "none"
        return "\n".join(
            [
                # blocks each live in their own mj-text (10px padding), so
                # margins stay at 0 and the rhythm comes from that padding
                f"h1, h2, h3, h4, h5, h6 {{ font-family: {heading_font};"
                f" color: {heading_color};"
                f" font-weight: {self.headings.font_weight};"
                f" line-height: 1.3; margin: 0; }}",
                f"h1 {{ font-size: {self.headings.h1_size}; }}",
                f"h2 {{ font-size: {self.headings.h2_size}; }}",
                f"h3 {{ font-size: {self.headings.h3_size}; }}",
                f"a {{ color: {self.links.color};"
                f" text-decoration: {decoration}; }}",
                f"blockquote {{ color: {self.quote.color};"
                f" font-style: {self.quote.font_style};"
                f" border-left: 3px solid {self.quote.border_color};"
                f" margin: 0; padding: 2px 0 2px 14px; }}",
                f"code {{ font-family: {self.code.font_family};"
                f" background-color: {self.code.background_color};"
                f" color: {self.code.color};"
                f" padding: 2px 4px; border-radius: 3px; }}",
                f"pre {{ font-family: {self.code.font_family};"
                f" background-color: {self.code.background_color};"
                f" color: {self.code.color};"
                f" margin: 0; padding: 12px; border-radius: 6px;"
                f" overflow-x: auto; }}",
                "ul, ol { margin: 0; padding-left: 24px; }",
                # note: no bare `table`/`td` selectors here — they would leak
                # onto the layout tables MJML generates for the email itself;
                # table cells are styled inline by the codegen instead
            ]
        )


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

# Standard, email-safe font stacks used by the presets
SANS = "Helvetica, Arial, sans-serif"
HUMANIST = "'Trebuchet MS', Helvetica, Arial, sans-serif"
WIDE_SANS = "Verdana, Geneva, sans-serif"
COMPACT_SANS = "Tahoma, Verdana, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"
ELEGANT_SERIF = "'Palatino Linotype', 'Book Antiqua', Palatino, Georgia, serif"


def _hue_theme(hue, text_font=SANS, heading_font=None):
    return Theme(
        layout=Layout(background_color=hue.LIGHTEST),
        text=Text(font_family=text_font),
        headings=Headings(color=hue.DARKEST, font_family=heading_font),
        links=Links(color=hue.DARK),
        quote=Quote(color=Gray.BASE, border_color=hue.LIGHT),
        divider=Divider(color=hue.LIGHT),
        code=Code(background_color=hue.LIGHTEST, color=hue.DARKEST),
        table=Table(
            border_color=hue.LIGHT,
            header_color=hue.DARKEST,
            header_background_color=hue.LIGHTEST,
        ),
    )


THEMES = {
    "default": Theme(),
    "dark": Theme(
        layout=Layout(
            background_color=Slate.DARKEST,
            content_background_color=Slate.DARK,
        ),
        text=Text(color=Slate.LIGHT),
        headings=Headings(color=WHITE, font_family=HUMANIST),
        links=Links(color=Blue.LIGHT),
        code=Code(background_color=Slate.DARKEST, color=Slate.LIGHT),
        quote=Quote(color=Slate.BASE, border_color=Slate.BASE),
        divider=Divider(color=Slate.BASE),
        table=Table(
            border_color=Slate.BASE,
            header_color=WHITE,
            header_background_color=Slate.DARKEST,
        ),
    ),
    "crystal": Theme(
        layout=Layout(background_color=Slate.LIGHTEST),
        text=Text(color=Slate.DARK),
        headings=Headings(color=Slate.DARKEST, font_family=ELEGANT_SERIF),
        links=Links(color=Blue.BASE),
        quote=Quote(color=Slate.BASE, border_color=Blue.LIGHT),
        divider=Divider(color=Slate.LIGHT),
        code=Code(background_color=Slate.LIGHTEST, color=Slate.DARKEST),
        table=Table(border_color=Slate.LIGHT, header_background_color=Slate.LIGHTEST),
    ),
    "blue": _hue_theme(Blue, text_font=COMPACT_SANS, heading_font=HUMANIST),
    "green": _hue_theme(Green, text_font=SERIF, heading_font=SERIF),
    "red": _hue_theme(Red, text_font=SANS, heading_font=SERIF),
    "yellow": _hue_theme(Yellow, text_font=WIDE_SANS, heading_font=HUMANIST),
}
