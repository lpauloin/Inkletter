from contextlib import contextmanager
from itertools import groupby
import html

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

    def __init__(self):
        super().__init__()
        self.root = CodeBlock()
        self.resolver = CodeBlockResolver()
        self.current = self.root

    def get_code(self):
        return self.resolver.resolve(self.root)

    @contextmanager
    def block_tag(self, name, attrs=None, self_closing=False, inline=False):
        attrs = attrs or {}
        attrs_str = "".join(
            f' {k}="{html.escape(str(v), quote=True)}"' for k, v in attrs.items()
        )
        if self_closing:
            self.current.add_text(f"<{name}{attrs_str}/>")
            if not inline:
                self.current.add_newline()
            yield
            return

        parent = self.current

        block = CodeBlock()
        if (
            not inline
            and parent.elements
            and isinstance(parent.elements[-1], TextElement)
        ):
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
            with self.block_tag("mj-text", inline=inline):
                yield
        else:
            yield

    def visit_Document(self, node, scope):
        with self.block_tag("mjml"):
            head = node.annotations["head"]
            if head is not None:
                self.emit_head(head)
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
            else:
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
            with self.block_tag("mj-attributes"):
                for tag, attrs in head["attributes"].items():
                    with self.block_tag(tag, attrs=attrs, self_closing=True):
                        pass
            with self.block_tag("mj-style", attrs={"inline": "inline"}):
                self.add_raw_lines(head["css"])

    def visit_Paragraph(self, node, scope):
        self.generic_visit(node, scope)

    def visit_Heading(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag(f"h{node.level}", inline=True):
                self.generic_visit(node, scope)

    def visit_BlockText(self, node, scope):
        with self.ensure_open_text(node):
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
        self.current.add_text("<br/>")
        self.current.add_newline()

    def visit_SoftBreak(self, node, scope):
        # Deliberate divergence from CommonMark (which renders a soft
        # break as a space): newsletter authors line-wrap on purpose,
        # a single newline in the source is a visible line break.
        self.current.add_text("<br/>")
        self.current.add_newline()

    def visit_BlankLine(self, node, scope):
        pass

    def visit_Image(self, node, scope):
        attrs = {"src": node.url}
        if node.alt_text:
            attrs["alt"] = node.alt_text.value
        if node.title:
            attrs["title"] = node.title

        if node.annotations.get("requires_manual_image"):
            tag = "img"
            attrs["style"] = node.annotations["image_style"]
        else:
            tag = "mj-image"
            if node.annotations.get("image_padding"):
                attrs["padding"] = node.annotations["image_padding"]

        with self.block_tag(tag, attrs=attrs, self_closing=True):
            pass

    def visit_ImageLink(self, node, scope):
        if node.img.annotations.get("requires_manual_image"):
            # href is not a valid <img> attribute: wrap in an anchor
            link_attrs = {"href": node.href}
            if node.title:
                link_attrs["title"] = node.title
            with self.block_tag("a", attrs=link_attrs, inline=True):
                img_attrs = {"src": node.img.url}
                if node.img.alt_text:
                    img_attrs["alt"] = node.img.alt_text.value
                if node.img.title:
                    img_attrs["title"] = node.img.title
                img_attrs["style"] = node.img.annotations["image_style"]

                with self.block_tag(
                    "img", attrs=img_attrs, self_closing=True, inline=True
                ):
                    pass
        else:
            attrs = {"src": node.img.url, "href": node.href}
            if node.img.alt_text:
                attrs["alt"] = node.img.alt_text.value
            if node.img.title:
                attrs["title"] = node.img.title
            if node.annotations.get("image_padding"):
                attrs["padding"] = node.annotations["image_padding"]

            with self.block_tag(
                "mj-image", attrs=attrs, self_closing=True, inline=True
            ):
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
        checkbox = "☑" if node.checked else "☐"
        # the checkbox replaces the bullet for this item only, so mixed
        # task/normal lists keep their bullets on normal items
        with self.block_tag("li", attrs={"style": "list-style-type: none;"}):
            block = node.children[0]
            assert isinstance(block, BlockText)
            self.current.add_text(checkbox + " ")
            for child in block.get_children():
                self.visit(child, scope)
            self.current.add_newline()
            for extra_child in node.children[1:]:
                self.visit(extra_child, scope)

    def visit_Table(self, node, scope):
        tag = (
            "table"
            if node.annotations.get("requires_manual_table", False)
            else "mj-table"
        )
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
        attrs = {"align": node.align} if node.align else {}
        attrs["style"] = node.annotations["cell_style"]
        with self.block_tag("th", attrs=attrs, inline=True):
            self.generic_visit(node, scope)
        self.current.add_newline()

    def visit_TableCell(self, node, scope):
        attrs = {"align": node.align} if node.align else {}
        attrs["style"] = node.annotations["cell_style"]
        with self.block_tag("td", attrs=attrs, inline=True):
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

    def visit_Link(self, node, scope):
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
        if node.annotations.get("requires_raw"):
            with self.block_tag("mj-raw"):
                self.add_raw_lines(node.value)
        else:
            self.add_raw_lines(node.value)

    def add_raw_lines(self, value):
        for line in value.splitlines():
            self.current.add_text(line)
            self.current.add_newline()

    def visit_CodeSpan(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("code", inline=True):
                self.current.add_text(html.escape(node.code))
