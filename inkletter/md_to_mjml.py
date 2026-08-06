from inkletter.ast import Document
from inkletter.codeblock import codeblock_from_string
from inkletter.django_tags import TagMask
from inkletter.md_to_ast import parse_markdown_to_ast
from inkletter.scope import ScopeStack
from inkletter.theme import DEFAULT_THEME
from inkletter.visitors.annotation import Annotation
from inkletter.visitors.codegen import Codegen
from inkletter.visitors.tree import print_tree


def render_mjml(
    markdown_text,
    print_ast=False,
    theme=None,
    bold_link_is_button=True,
    url_factory=None,
    django_tags=False,
):
    """The masked MJML, and the mask that reveals its Django tags.

    Callers that compile the MJML (parse_markdown_to_html, the preview)
    must hand mjml2html the masked version — its XML parser chokes on
    the < of a tag — and reveal afterwards, on the HTML.
    """
    ast = parse_markdown_to_ast(
        markdown_text,
        bold_link_is_button=bold_link_is_button,
        theme=theme,
        url_factory=url_factory,
        django_tags=django_tags,
    )
    if print_ast:
        print_tree(ast)
    mask = TagMask(markdown_text)
    codegen = Codegen(mask)
    codegen.visit(ast)
    return codegen.get_code(), mask


def parse_markdown_to_mjml(
    markdown_text,
    print_ast=False,
    theme=None,
    bold_link_is_button=True,
    url_factory=None,
    django_tags=False,
):
    mjml, mask = render_mjml(
        markdown_text,
        print_ast=print_ast,
        theme=theme,
        bold_link_is_button=bold_link_is_button,
        url_factory=url_factory,
        django_tags=django_tags,
    )
    return mask.reveal(mjml)


def wrap_mjml_document(body_content):
    """Wrap raw body content (sections) in the default-themed document.

    The head and body attributes come from the real Annotation pass on an
    empty Document: no duplication of the theme rendering.
    """
    if isinstance(body_content, str):
        body_content = codeblock_from_string(body_content)

    document = Document([])
    Annotation(DEFAULT_THEME).visit(document, scope=ScopeStack())

    codegen = Codegen(TagMask())
    with codegen.block_tag("mjml"):
        codegen.emit_head(document.annotations["head"])
        with codegen.block_tag("mj-body", attrs=document.annotations["body_attrs"]):
            codegen.current.add_codeblock(body_content)
    return codegen.get_code()


def wrap_mjml_body(content):
    """Wrap flow content in the default-themed document, one section/column."""
    if isinstance(content, str):
        content = codeblock_from_string(content)

    document = Document([])
    Annotation(DEFAULT_THEME).visit(document, scope=ScopeStack())

    codegen = Codegen(TagMask())
    with codegen.block_tag("mjml"):
        codegen.emit_head(document.annotations["head"])
        with codegen.block_tag("mj-body", attrs=document.annotations["body_attrs"]):
            with codegen.block_tag("mj-section"):
                with codegen.block_tag("mj-column"):
                    codegen.current.add_codeblock(content)
    return codegen.get_code()
