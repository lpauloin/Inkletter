from inkletter.ast import Document
from inkletter.codeblock import codeblock_from_string
from inkletter.md_to_ast import parse_markdown_to_ast
from inkletter.theme import DEFAULT_THEME
from inkletter.visitors.annotation import Annotation
from inkletter.visitors.codegen import Codegen
from inkletter.visitors.tree import print_tree


def parse_markdown_to_mjml(
    markdown_text,
    print_ast=False,
    theme=None,
    bold_link_is_button=True,
    url_factory=None,
):
    ast = parse_markdown_to_ast(
        markdown_text,
        bold_link_is_button=bold_link_is_button,
        theme=theme,
        url_factory=url_factory,
    )
    if print_ast:
        print_tree(ast)
    codegen = Codegen()
    codegen.visit(ast)
    return codegen.get_code()


def wrap_mjml_document(body_content, title=None):
    """Wrap raw body content (sections) in the default-themed document.

    The head and body attributes come from the real Annotation pass on an
    empty Document: no duplication of the theme rendering. `title` is
    what a document opening with a plain-text h1 gets in its head.
    """
    if isinstance(body_content, str):
        body_content = codeblock_from_string(body_content)

    document = Document([])
    Annotation(DEFAULT_THEME).visit(document)
    document.annotations["head"]["title"] = title

    codegen = Codegen()
    with codegen.block_tag("mjml"):
        codegen.emit_head(document.annotations["head"])
        with codegen.block_tag("mj-body", attrs=document.annotations["body_attrs"]):
            codegen.current.add_codeblock(body_content)
    return codegen.get_code()


def wrap_mjml_body(content, title=None):
    """Same, for flow content that belongs in one section and column."""
    if isinstance(content, str):
        content = codeblock_from_string(content)

    codegen = Codegen()
    with codegen.block_tag("mj-section"):
        with codegen.block_tag("mj-column"):
            codegen.current.add_codeblock(content)
    return wrap_mjml_document(codegen.root, title=title)
