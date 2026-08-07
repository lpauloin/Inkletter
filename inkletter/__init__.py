"""Inkletter: Markdown to responsive MJML/HTML emails."""

from importlib.metadata import PackageNotFoundError, version

from inkletter.escaping import escape_markdown
from inkletter.exceptions import ThemeError
from inkletter.md_to_html import parse_markdown_to_html, parse_mjml_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.md_to_text import parse_markdown_to_text
from inkletter.shortener import BitlyShortener, URLFactory
from inkletter.theme import THEMES, Theme

try:
    __version__ = version("inkletter")
except PackageNotFoundError:  # not installed (e.g. sources on sys.path)
    __version__ = "0.0.0"

__all__ = [
    "escape_markdown",
    "parse_markdown_to_mjml",
    "parse_markdown_to_html",
    "parse_markdown_to_text",
    "parse_mjml_to_html",
    "Theme",
    "ThemeError",
    "THEMES",
    "URLFactory",
    "BitlyShortener",
    "__version__",
]
