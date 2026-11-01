"""The public API as a caller writes it, checked by `mypy --strict` (the CI
runs it): the `py.typed` marker promises a typed package, and this holds the
promise. Never run, only read."""

from inkletter import (
    THEMES,
    BitlyShortener,
    LengthError,
    LinkedinRender,
    Theme,
    URLFactory,
    __version__,
    escape_markdown,
    parse_markdown_to_html,
    parse_markdown_to_html_fragment,
    parse_markdown_to_linkedin,
    parse_markdown_to_mjml,
    parse_markdown_to_text,
    parse_mjml_to_html,
    render_linkedin,
    runs_something,
)


class Tagging(URLFactory):
    link_length = 26

    def rewrite_link(self, url: str, is_button: bool = False, is_bold: bool = False) -> str:
        return f"{url}?button={is_button}&bold={is_bold}"


def every_output(markdown: str) -> list[str]:
    theme: Theme = Theme.named("dark")
    dark: Theme = THEMES["dark"]
    mjml: str = parse_markdown_to_mjml(markdown, theme=theme, url_factory=Tagging(), lang="en")
    return [
        mjml,
        parse_mjml_to_html(mjml),
        parse_markdown_to_html(markdown, theme=dark, lang="fr"),
        parse_markdown_to_html_fragment(markdown, link_attributes=False),
        parse_markdown_to_text(markdown, bold_link_is_button=False),
        parse_markdown_to_linkedin(markdown, unicode_styling=True, max_length=None),
        escape_markdown(42),
        Theme.from_dict({"links": {"color": "#0a66c2"}}).to_css(),
        BitlyShortener("token").rewrite_image("https://exemple.fr/a.png"),
        __version__,
    ]


def what_the_feed_shows(markdown: str) -> tuple[str, int, bool, bool, frozenset[str], list[str]]:
    render: LinkedinRender = render_linkedin(markdown, url_factory=Tagging())
    kinds = [segment.kind for line in render.lines for segment in line.segments]
    return (
        render.shown_text,
        render.length,
        render.unrendered_formatting,
        render.unrendered_headings,
        render.styles,
        kinds,
    )


def what_a_link_bar_refuses(address: str) -> bool:
    linked: bool = not runs_something(address)
    return linked


def what_a_refusal_says(markdown: str) -> int:
    try:
        parse_markdown_to_linkedin(markdown, max_length=10)
    except LengthError as refusal:
        return refusal.length - refusal.limit
    return 0
