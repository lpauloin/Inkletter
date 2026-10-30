from mjml import mjml2html

from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.shortener import URLFactory
from inkletter.theme import Theme


def parse_mjml_to_html(mjml_text: str) -> str:
    return mjml2html(mjml_text)


def parse_markdown_to_html(
    markdown_text: str,
    theme: Theme | None = None,
    bold_link_is_button: bool = True,
    link_attributes: bool = True,
    url_factory: URLFactory | None = None,
) -> str:
    return parse_mjml_to_html(
        parse_markdown_to_mjml(
            markdown_text,
            theme=theme,
            bold_link_is_button=bold_link_is_button,
            link_attributes=link_attributes,
            url_factory=url_factory,
        )
    )
