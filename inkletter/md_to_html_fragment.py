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
) -> str:
    """The document as a fragment of HTML, to set inside another page."""
    ast = parse_markdown_to_ast(
        markdown_text,
        bold_link_is_button=bold_link_is_button,
        link_attributes=link_attributes,
        url_factory=url_factory,
    )
    if print_ast:
        print_tree(ast)
    codegen = HtmlFragmentCodegen()
    codegen.visit(ast)
    return codegen.get_html()
