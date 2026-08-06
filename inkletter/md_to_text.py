from inkletter.md_to_ast import parse_markdown_to_ast
from inkletter.visitors.textgen import TextCodegen
from inkletter.visitors.tree import print_tree


def parse_markdown_to_text(
    markdown_text, print_ast=False, bold_link_is_button=True, url_factory=None
):
    """The plain-text alternative of the email (multipart/alternative)."""
    ast = parse_markdown_to_ast(
        markdown_text,
        bold_link_is_button=bold_link_is_button,
        url_factory=url_factory,
    )
    if print_ast:
        print_tree(ast)
    codegen = TextCodegen()
    codegen.visit(ast)
    return codegen.get_text()
