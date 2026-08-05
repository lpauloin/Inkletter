from contextlib import contextmanager
from itertools import groupby
import html

from inkletter.ast import *
from inkletter.codeblock import (
    CodeBlock,
    CodeBlockResolver,
    TextElement,
)
from inkletter.theme import split_media_ratio
from inkletter.visitors.generic import NodeVisitor


class Codegen(NodeVisitor):
    def __init__(self, theme=None):
        super().__init__()
        self.root = CodeBlock()
        self.resolver = CodeBlockResolver()
        self.current = self.root
        self.theme = theme

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
        # The document is a sequence of bands: consecutive ordinary blocks
        # share one section/column, while nodes annotated own_section
        # (image rows, media objects) generate their own section.
        with self.block_tag("mjml"):
            body_attrs = {}
            if self.theme is not None:
                self.emit_head(self.theme)
                body_attrs = {
                    "width": self.theme.layout.width,
                    "background-color": self.theme.layout.background_color,
                }
            with self.block_tag("mj-body", attrs=body_attrs):
                own_section = lambda c: bool(c.annotations.get("own_section"))
                for standalone, band in groupby(node.children, key=own_section):
                    if standalone:
                        for child in band:
                            self.visit(child, scope)
                    else:
                        with self.block_tag("mj-section"):
                            with self.block_tag("mj-column"):
                                for child in band:
                                    self.visit(child, scope)

    def visit_ImageRow(self, node, scope):
        with self.block_tag("mj-section"):
            for image in node.children:
                with self.block_tag("mj-column"):
                    self.visit(image, scope)

    def visit_MediaObject(self, node, scope):
        if self.theme is not None and self.theme.images.text_layout == "stacked":
            with self.block_tag("mj-section"):
                with self.block_tag("mj-column"):
                    self.visit(node.image, scope)
                    for child in node.children:
                        self.visit(child, scope)
            return

        ratio = self.theme.images.media_ratio if self.theme is not None else "30%"
        image_width, text_width = split_media_ratio(ratio)
        # DOM order keeps the image first so it stacks on top on mobile;
        # side=right is a desktop-only visual flip through direction=rtl.
        attrs = {"direction": "rtl"} if node.side == "right" else {}
        with self.block_tag("mj-section", attrs=attrs):
            with self.block_tag("mj-column", attrs={"width": image_width}):
                self.visit(node.image, scope)
            with self.block_tag("mj-column", attrs={"width": text_width}):
                for child in node.children:
                    self.visit(child, scope)

    def row_image_padding(self):
        gap = self.theme.images.row_gap if self.theme is not None else "8px"
        return f"10px {gap}"

    def emit_head(self, theme):
        with self.block_tag("mj-head"):
            with self.block_tag("mj-attributes"):
                with self.block_tag(
                    "mj-section",
                    attrs={
                        "padding": theme.layout.section_padding,
                        "background-color": theme.layout.content_background_color,
                    },
                    self_closing=True,
                ):
                    pass
                with self.block_tag(
                    "mj-text",
                    attrs={
                        "font-family": theme.text.font_family,
                        "font-size": theme.text.font_size,
                        "line-height": theme.text.line_height,
                        "color": theme.text.color,
                    },
                    self_closing=True,
                ):
                    pass
                # mj-table has its own MJML defaults (black Ubuntu 13px)
                # that would ignore the theme typography
                with self.block_tag(
                    "mj-table",
                    attrs={
                        "color": theme.text.color,
                        "font-family": theme.text.font_family,
                        "font-size": theme.text.font_size,
                        "line-height": theme.text.line_height,
                    },
                    self_closing=True,
                ):
                    pass
                with self.block_tag(
                    "mj-divider",
                    attrs={
                        "border-color": theme.divider.color,
                        "border-width": theme.divider.width,
                    },
                    self_closing=True,
                ):
                    pass
                image_attrs = {
                    "fluid-on-mobile": "true",
                    "align": theme.images.align,
                }
                if theme.images.border_radius not in ("0", "0px"):
                    image_attrs["border-radius"] = theme.images.border_radius
                with self.block_tag(
                    "mj-image",
                    attrs=image_attrs,
                    self_closing=True,
                ):
                    pass
            with self.block_tag("mj-style", attrs={"inline": "inline"}):
                self.add_raw_lines(theme.to_css())

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
        # With a theme the styling comes from mj-attributes in the head.
        if self.theme is not None:
            attrs = {}
        else:
            attrs = {"border-color": "#cccccc", "border-width": "1px"}
        with self.block_tag("mj-divider", attrs=attrs, self_closing=True):
            pass

    def visit_LineBreak(self, node, scope):
        self.current.add_text("<br/>")
        self.current.add_newline()

    def visit_SoftBreak(self, node, scope):
        self.current.add_text("<br/>")
        self.current.add_newline()

    def visit_BlankLine(self, node, scope):
        pass

    def image_style(self):
        style = "max-width: 100%; height: auto;"
        if self.theme is not None:
            radius = self.theme.images.border_radius
            if radius not in ("0", "0px"):
                style += f" border-radius: {radius};"
        return style

    def visit_Image(self, node, scope):
        attrs = {"src": node.url}
        if node.alt_text:
            attrs["alt"] = node.alt_text.value
        if node.title:
            attrs["title"] = node.title

        if node.annotations.get("requires_manual_image"):
            tag = "img"
            attrs["style"] = self.image_style()
        else:
            tag = "mj-image"
            if node.annotations.get("in_image_row"):
                attrs["padding"] = self.row_image_padding()

        with self.block_tag(tag, attrs=attrs, self_closing=True):
            pass

    def visit_ImageLink(self, node, scope):
        attrs = {"src": node.img.url, "href": node.href}
        if node.img.alt_text:
            attrs["alt"] = node.img.alt_text.value
        if node.img.title:
            attrs["title"] = node.img.title

        if node.img.annotations.get("requires_manual_image"):
            tag = "img"
            attrs["style"] = self.image_style()
        else:
            tag = "mj-image"
            if node.annotations.get("in_image_row"):
                attrs["padding"] = self.row_image_padding()

        with self.block_tag(tag, attrs=attrs, self_closing=True, inline=True):
            pass

    def visit_List(self, node, scope):
        with self.ensure_open_text(node):
            tag = "ol" if node.ordered else "ul"
            attrs = (
                {"style": "list-style-type: none;"}
                if node.annotations.get("is_task_list")
                else {}
            )
            with self.block_tag(tag, attrs=attrs):
                self.generic_visit(node, scope)

    def visit_ListItem(self, node, scope):
        with self.block_tag("li"):
            self.generic_visit(node, scope)

    def visit_TaskListItem(self, node, scope):
        checkbox = "☑" if node.checked else "☐"
        with self.block_tag("li"):
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
        if self.theme is not None:
            table = self.theme.table
            style = (
                f"border-bottom: 2px solid {table.border_color};"
                f" padding: {table.cell_padding};"
            )
            if table.header_color:
                style += f" color: {table.header_color};"
            if table.header_background_color:
                style += f" background-color: {table.header_background_color};"
            if not node.align:
                style += " text-align: left;"
            attrs["style"] = style
        with self.block_tag("th", attrs=attrs, inline=True):
            self.generic_visit(node, scope)
        self.current.add_newline()

    def visit_TableCell(self, node, scope):
        attrs = {"align": node.align} if node.align else {}
        if self.theme is not None:
            table = self.theme.table
            attrs["style"] = (
                f"border-bottom: 1px solid {table.border_color};"
                f" padding: {table.cell_padding};"
            )
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
