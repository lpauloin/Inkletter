from inkletter.md_to_ast import parse_markdown_to_ast
from inkletter.shortener import URLFactory
from inkletter.visitors.textgen import TextCodegen
from inkletter.visitors.tree import print_tree


def parse_markdown_to_text(
    markdown_text: str,
    print_ast: bool = False,
    bold_link_is_button: bool = True,
    link_attributes: bool = True,
    url_factory: URLFactory | None = None,
) -> str:
    """The plain-text alternative of the email (multipart/alternative)."""
    ast = parse_markdown_to_ast(
        markdown_text,
        bold_link_is_button=bold_link_is_button,
        link_attributes=link_attributes,
        url_factory=url_factory,
    )
    if print_ast:
        print_tree(ast)
    codegen = TextCodegen()
    codegen.visit(ast)
    return codegen.get_text()
