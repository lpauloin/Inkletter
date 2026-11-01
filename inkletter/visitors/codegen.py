import html
from contextlib import contextmanager
from itertools import groupby

from inkletter.ast import *
from inkletter.codeblock import (
    CodeBlock,
    CodeBlockResolver,
    TextElement,
)
from inkletter.visitors.generic import NodeVisitor


class Codegen(NodeVisitor):
    """Emits MJML from the annotated AST. Every styling decision reaches
    it as annotation-provided instructions: no theme in sight."""

    def __init__(self, lang=None):
        super().__init__()
        self.lang = lang
        self.root = CodeBlock()
        self.resolver = CodeBlockResolver()
        self.current = self.root

    def get_code(self):
        return self.resolver.resolve(self.root)

    @contextmanager
    def block_tag(self, name, attrs=None, self_closing=False, inline=False):
        attrs = attrs or {}
        attrs_str = "".join(f' {k}="{html.escape(str(v), quote=True)}"' for k, v in attrs.items())
        if self_closing:
            self.current.add_text(f"<{name}{attrs_str}/>")
            if not inline:
                self.current.add_newline()
            yield
            return

        parent = self.current

        block = CodeBlock()
        if not inline and parent.elements and isinstance(parent.elements[-1], TextElement):
            block.add_newline()

        block.add_text(f"<{name}{attrs_str}>")

        if not inline:
            block.add_newline()
            block.add_indent()

        parent.add_codeblock(block)
        self.current = block

        yield

        self.current = parent
        if not inline:
            last_element = parent.elements[-1]
            assert last_element == block
            if isinstance(last_element.elements[-1], TextElement):
                last_element.add_newline()
            self.current.add_dedent()

        self.current.add_text(f"</{name}>")

        if not inline:
            self.current.add_newline()

    @contextmanager
    def ensure_open_text(self, node, inline=False):
        if node.annotations.get("requires_text"):
            with self.block_tag("mj-text", attrs=node.annotations.get("text_attrs"), inline=inline):
                yield
        else:
            yield

    def root_attrs(self):
        """The root's attributes: the language the email is written in, when
        given — MJML carries it to `<html>`, where a screen reader picks its
        voice."""
        return {"lang": self.lang} if self.lang else None

    def visit_Document(self, node, scope):
        with self.block_tag("mjml", attrs=self.root_attrs()):
            self.emit_head(node.annotations["head"])
            with self.block_tag("mj-body", attrs=node.annotations["body_attrs"]):
                self.emit_bands(node.children, scope)

    def defines_own_columns(self, node):
        return bool(node.annotations.get("defines_own_columns"))

    def emit_bands(self, children, scope):
        """The document body alternates two kinds of bands: blocks that
        stack in a single column share one flow section, while nodes
        defining their own column layout (image rows, media objects)
        emit their own mj-section through their visitor."""
        for multi_column, band in groupby(children, key=self.defines_own_columns):
            if multi_column:
                for node in band:
                    self.visit(node, scope)
                continue
            band = list(band)
            # the blank lines between two bands of their own are no band:
            # an empty section would only add its padding
            if all(isinstance(node, BlankLine) for node in band):
                continue
            self.emit_flow_band(band, scope)

    def emit_flow_band(self, children, scope):
        with self.block_tag("mj-section"):
            with self.block_tag("mj-column"):
                for child in children:
                    self.visit(child, scope)

    def visit_Button(self, node, scope):
        attrs = {"href": node.href}
        if node.title:
            attrs["title"] = node.title
        with self.block_tag("mj-button", attrs=attrs, inline=True):
            self.generic_visit(node, scope)
        self.current.add_newline()

    def visit_ImageRow(self, node, scope):
        with self.block_tag("mj-section"):
            for image in node.children:
                with self.block_tag("mj-column"):
                    self.visit(image, scope)

    def visit_MediaObject(self, node, scope):
        # The Annotation pass decided the layout and all its parameters.
        emitters = {
            "stacked": self.emit_media_stacked,
            "columns": self.emit_media_columns,
        }
        emitters[node.annotations["media_layout"]](node, scope)

    def emit_media_stacked(self, node, scope):
        with self.block_tag("mj-section"):
            with self.block_tag("mj-column"):
                self.visit(node.image, scope)
                for child in node.children:
                    self.visit(child, scope)

    def emit_media_columns(self, node, scope):
        image_width, text_width = node.annotations["media_widths"]
        attrs = {}
        if node.annotations["media_direction"]:
            attrs["direction"] = node.annotations["media_direction"]
        with self.block_tag("mj-section", attrs=attrs):
            with self.block_tag("mj-column", attrs={"width": image_width}):
                self.visit(node.image, scope)
            with self.block_tag("mj-column", attrs={"width": text_width}):
                for child in node.children:
                    self.visit(child, scope)

    def emit_head(self, head):
        with self.block_tag("mj-head"):
            if head["title"]:
                with self.block_tag("mj-title", inline=True):
                    self.current.add_text(html.escape(head["title"], quote=False))
                self.current.add_newline()
            for name, href in head["fonts"]:
                with self.block_tag(
                    "mj-font", attrs={"name": name, "href": href}, self_closing=True
                ):
                    pass
            with self.block_tag("mj-attributes"):
                for tag, attrs in head["attributes"].items():
                    with self.block_tag(tag, attrs=attrs, self_closing=True):
                        pass
            with self.block_tag("mj-style", attrs={"inline": "inline"}):
                self.add_raw_lines(head["css"])

    def visit_Paragraph(self, node, scope):
        if node.annotations.get("requires_paragraph_tag"):
            with self.block_tag("p", inline=True):
                self.checkbox(node)
                self.generic_visit(node, scope)
        else:
            self.checkbox(node)
            self.generic_visit(node, scope)

    def checkbox(self, node):
        """The box a task item's first line opens on."""
        box = node.annotations.get("checkbox")
        if box:
            self.current.add_text(box + " ")

    def visit_Heading(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag(f"h{node.level}", inline=True):
                self.generic_visit(node, scope)

    def visit_BlockText(self, node, scope):
        with self.ensure_open_text(node):
            self.checkbox(node)
            self.generic_visit(node, scope)

    def visit_BlockQuote(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("blockquote"):
                self.generic_visit(node, scope)

    def visit_BlockCode(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("pre"):
                self.current.add_text(html.escape(node.code), indented=False)

    def visit_ThematicBreak(self, node, scope):
        with self.block_tag(
            "mj-divider",
            attrs=node.annotations["divider_attrs"],
            self_closing=True,
        ):
            pass

    def visit_LineBreak(self, node, scope):
        self.line_break(node)

    def visit_SoftBreak(self, node, scope):
        # Deliberate divergence from CommonMark (which renders a soft
        # break as a space): newsletter authors line-wrap on purpose,
        # a single newline in the source is a visible line break.
        self.line_break(node)

    def line_break(self, node):
        # beside an image stacked as a block, the stacking is the break
        if node.annotations.get("between_blocks"):
            return
        self.current.add_text("<br/>")
        self.current.add_newline()

    def visit_BlankLine(self, node, scope):
        pass

    @staticmethod
    def image_attrs(img, href=None, padding=None):
        """An image's attributes: a plain <img> takes its style, an
        mj-image its link, its spacing in a row and the author's size. An
        alt always, empty for an image that says nothing."""
        attrs = {"src": img.url}
        if href:
            attrs["href"] = href
        attrs["alt"] = img.alt_text
        if img.title:
            attrs["title"] = img.title
        if img.annotations.get("requires_manual_image"):
            attrs["style"] = img.annotations["image_style"]
            return attrs
        if padding:
            attrs["padding"] = padding
        attrs.update(img.annotations.get("image_size", {}))
        return attrs

    def visit_Image(self, node, scope):
        tag = "img" if node.annotations.get("requires_manual_image") else "mj-image"
        attrs = self.image_attrs(node, padding=node.annotations.get("image_padding"))
        with self.block_tag(tag, attrs=attrs, self_closing=True):
            pass

    def visit_ImageLink(self, node, scope):
        if node.img.annotations.get("requires_manual_image"):
            # href is not a valid <img> attribute: wrap in an anchor
            link_attrs = {"href": node.href}
            if node.title:
                link_attrs["title"] = node.title
            with self.block_tag("a", attrs=link_attrs, inline=True):
                with self.block_tag(
                    "img", attrs=self.image_attrs(node.img), self_closing=True, inline=True
                ):
                    pass
            return
        attrs = self.image_attrs(
            node.img, href=node.href, padding=node.annotations.get("image_padding")
        )
        with self.block_tag("mj-image", attrs=attrs, self_closing=True, inline=True):
            pass

    def visit_List(self, node, scope):
        with self.ensure_open_text(node):
            tag = "ol" if node.ordered else "ul"
            attrs = {}
            if node.ordered and node.start not in (None, 1):
                attrs["start"] = node.start
            with self.block_tag(tag, attrs=attrs):
                self.generic_visit(node, scope)

    def visit_ListItem(self, node, scope):
        with self.block_tag("li"):
            self.generic_visit(node, scope)

    def visit_TaskListItem(self, node, scope):
        # the checkbox replaces the bullet for this item only, so mixed
        # task/normal lists keep their bullets on normal items
        with self.block_tag("li", attrs={"style": "list-style-type: none;"}):
            self.generic_visit(node, scope)

    def visit_Table(self, node, scope):
        tag = "table" if node.annotations.get("requires_manual_table", False) else "mj-table"
        with self.block_tag(tag):
            if node.header:
                self.visit(node.header, scope)
            for row in node.rows:
                self.visit(row, scope)

    def visit_TableHeader(self, node, scope):
        with self.block_tag("tr"):
            for head in node.headers:
                self.visit(head, scope)

    def visit_TableRow(self, node, scope):
        with self.block_tag("tr"):
            for cell in node.row:
                self.visit(cell, scope)

    def visit_TableHeaderCell(self, node, scope):
        self.cell("th", node, scope)

    def visit_TableCell(self, node, scope):
        self.cell("td", node, scope)

    def cell(self, tag, node, scope):
        attrs = {"align": node.align} if node.align else {}
        attrs["style"] = node.annotations["cell_style"]
        with self.block_tag(tag, attrs=attrs, inline=True):
            self.generic_visit(node, scope)
        self.current.add_newline()

    def visit_LiteralText(self, node, scope):
        with self.ensure_open_text(node):
            self.current.add_text(html.escape(node.value, quote=False))

    def visit_Emphasis(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("em", inline=True):
                self.generic_visit(node, scope)

    def visit_Strong(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("strong", inline=True):
                self.generic_visit(node, scope)

    def visit_StrikeThrough(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("del", inline=True):
                self.generic_visit(node, scope)

    def visit_UrlLink(self, node, scope):
        self.anchor(node, scope)

    def visit_MailLink(self, node, scope):
        self.anchor(node, scope)

    def visit_TelLink(self, node, scope):
        self.anchor(node, scope)

    def anchor(self, node, scope):
        with self.ensure_open_text(node):
            attrs = {"href": node.href}
            if node.title:
                attrs["title"] = node.title
            with self.block_tag("a", attrs=attrs, inline=True):
                self.generic_visit(node, scope)

    def visit_InlineHtml(self, node, scope):
        with self.ensure_open_text(node):
            self.current.add_text(node.value)

    def visit_BlockHtml(self, node, scope):
        # verbatim, wrapped in mj-raw when it sits at flow level
        if node.annotations.get("requires_raw"):
            with self.block_tag("mj-raw"):
                self.add_raw_lines(node.value)
        else:
            self.add_raw_lines(node.value)

    def add_raw_lines(self, value):
        for line in value.splitlines():
            self.current.add_text(line)
            self.current.add_newline()

    def visit_Hashtag(self, node, scope):
        with self.ensure_open_text(node):
            style = node.annotations.get("hashtag_style")
            if style:
                with self.block_tag("span", attrs={"style": style}, inline=True):
                    self.current.add_text(f"#{node.name}")
            else:
                self.current.add_text(f"#{node.name}")

    def visit_CodeSpan(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("code", inline=True):
                self.current.add_text(html.escape(node.code))
