import unicodedata
from collections.abc import Callable

from inkletter.md_to_ast import parse_markdown_to_ast
from inkletter.shortener import URLFactory
from inkletter.visitors.htmlgen import HtmlFragmentCodegen
from inkletter.visitors.tree import print_tree


def parse_markdown_to_html_fragment(
    markdown_text: str,
    print_ast: bool = False,
    bold_link_is_button: bool = True,
    link_attributes: bool = True,
    url_factory: URLFactory | None = None,
    images: bool = False,
    mentions: Callable[[str], dict[str, str] | None] | None = None,
    unicode_strike: bool = False,
    task_paragraphs: bool = False,
    heading_offset: int = 0,
) -> str:
    """The document as a fragment of HTML, to set inside another page. Its
    pictures are their alternative text, unless `images` asks for them —
    for a page that serves the addresses itself; its mentions, its
    strikethrough and its lists of tasks written as `mentions`,
    `unicode_strike` and `task_paragraphs` ask (see HtmlFragmentCodegen).
    `heading_offset` is added to every heading's level, held between 1
    and 6.

    Accents are composed first (NFC), as the post composes them: a letter
    and its accent are one character, which a look-alike strikes as one."""
    ast = parse_markdown_to_ast(
        unicodedata.normalize("NFC", markdown_text),
        bold_link_is_button=bold_link_is_button,
        link_attributes=link_attributes,
        url_factory=url_factory,
        heading_offset=heading_offset,
    )
    if print_ast:
        print_tree(ast)
    codegen = HtmlFragmentCodegen(
        images=images,
        mentions=mentions,
        unicode_strike=unicode_strike,
        task_paragraphs=task_paragraphs,
    )
    codegen.visit(ast)
    return codegen.get_html()
