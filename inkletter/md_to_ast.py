import html

import mistune

from inkletter.ast import *
from inkletter.link_attributes import link_attributes as link_attributes_plugin
from inkletter.theme import DEFAULT_THEME
from inkletter.visitors.annotation import Annotation
from inkletter.visitors.merger import BlockTextMerger
from inkletter.visitors.urls import URLRewriter


class ASTRenderer(mistune.BaseRenderer):
    def render_token(self, token, state):
        func = self._get_method(token["type"])
        attrs = token.get("attrs")

        if "raw" in token:
            text = token["raw"]
        elif "children" in token:
            text = self.render_tokens(token["children"], state)
        else:
            text = None

        if attrs:
            if text is not None:
                node = func(text, **attrs)
            else:
                node = func(**attrs)
        else:
            if text is not None:
                node = func(text)
            else:
                node = func()

        return node

    def render_tokens(self, tokens, state):
        nodes = []
        for token in tokens:
            rv = self.render_token(token, state)
            if rv is None:
                continue
            if isinstance(rv, list):
                nodes.extend(rv)
            else:
                nodes.append(rv)
        return nodes

    def __call__(self, tokens, state):
        return Document(self.render_tokens(tokens, state))

    # --- Inline renderers ---

    def text(self, value):
        # CommonMark decodes HTML entities everywhere but in code:
        # mistune hands the raw text over, unescape it here (the codegen
        # re-escapes for HTML output, so &amp; round-trips correctly)
        return LiteralText(html.unescape(value))

    def emphasis(self, text):
        return Emphasis(text)

    def strong(self, text):
        return Strong(text)

    def strikethrough(self, text):
        return StrikeThrough(text)

    def codespan(self, text):
        return CodeSpan(text)

    def inline_html(self, html):
        return InlineHtml(html)

    def link(self, text, url, title=None, ink_attributes=None):
        # If the text contains an image, we create an ImageLink
        # We extract the image from the text to create a new ImageLink node
        # The rest of the text is ignored
        title = html.unescape(title) if title else title
        if img := next((t for t in text if isinstance(t, Image)), None):
            # a block written after the link decorates the image it wraps,
            # so both spellings land in the same place
            if ink_attributes and not img.attributes:
                img.attributes = Attributes(**ink_attributes)
            return ImageLink(img, url, title)
        else:
            return Link(text, url, title)

    # --- Block renderers ---

    def paragraph(self, text):
        return Paragraph(text)

    def heading(self, text, level):
        return Heading(level, text)

    def block_code(self, code, info=None):
        language = info.strip() if info else None
        return BlockCode(code, language)

    def block_text(self, text):
        return BlockText(text)

    def block_html(self, html):
        return BlockHtml(html.strip("\n"))

    def thematic_break(self):
        return ThematicBreak()

    def blank_line(self):
        return BlankLine()

    def linebreak(self):
        return LineBreak()

    def softbreak(self):
        return SoftBreak()

    def block_quote(self, text):
        return BlockQuote(text)

    def image(self, alt, url, title=None, ink_attributes=None):
        # The tokenizer returns a list of inline nodes; the alt may contain
        # formatting, which BlockTextMerger later merges into a single
        # LiteralText since the HTML alt attribute cannot hold markup.
        if alt:
            assert isinstance(alt, list), alt
        title = html.unescape(title) if title else title
        return Image(url, alt, title, attributes=Attributes(**(ink_attributes or {})))

    # --- List renderers ---

    def list(self, elements, ordered, **attrs):
        return List(elements, ordered=ordered, start=attrs.get("start"))

    def list_item(self, element, **attrs):
        return ListItem(element)

    # --- Task renderers ---

    def task_list_item(self, text, checked=False):
        return TaskListItem(text, checked)

    # --- Table renderers ---

    def table(self, children):
        header = next(filter(lambda c: isinstance(c, TableHeader), children))
        rows = list(filter(lambda c: isinstance(c, TableRow), children))
        return Table(header=header, rows=rows)

    def table_body(self, text):
        return text

    def table_head(self, text):
        return TableHeader(text)

    def table_row(self, content):
        return TableRow(content)

    def table_cell(self, text, align=None, head=False):
        if head:
            return TableHeaderCell(text, align=align)
        else:
            return TableCell(text, align=align)


def parse_markdown_to_ast(
    markdown_text,
    bold_link_is_button=True,
    link_attributes=True,
    theme=None,
    url_factory=None,
):
    renderer = ASTRenderer()
    plugins = [
        "mistune.plugins.formatting.strikethrough",
        "mistune.plugins.table.table",
        "mistune.plugins.table.table_in_list",
        "mistune.plugins.table.table_in_quote",
        "mistune.plugins.task_lists.task_lists",
    ]
    if link_attributes:
        plugins.append(link_attributes_plugin)

    markdown = mistune.create_markdown(renderer=renderer, plugins=plugins)

    ast = markdown(markdown_text)

    if url_factory is not None:
        URLRewriter(url_factory).visit(ast)

    if theme is None:
        theme = DEFAULT_THEME

    BlockTextMerger(bold_link_is_button=bold_link_is_button).visit(ast)
    Annotation(theme=theme).visit(ast)

    return ast
