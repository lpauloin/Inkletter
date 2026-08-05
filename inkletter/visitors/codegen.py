from contextlib import contextmanager
import html

from inkletter.ast import *
from inkletter.codeblock import (
    CodeBlock,
    CodeBlockResolver,
    TextElement,
)
from inkletter.visitors.generic import NodeVisitor


class Codegen(NodeVisitor):
    def __init__(self, use_style=False):
        super().__init__()
        self.root = CodeBlock()
        self.resolver = CodeBlockResolver()
        self.current = self.root
        self.use_style = use_style

    def get_code(self):
        return self.resolver.resolve(self.root)

    @contextmanager
    def block_tag(self, name, attrs=None, self_closing=False, inline=False):
        attrs = attrs or {}
        attrs_str = "".join(f' {k}="{v}"' for k, v in attrs.items())
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
    def ensure_open_column(self, node):
        if node.annotations.get("requires_column"):
            with self.block_tag("mj-section"):
                with self.block_tag("mj-column"):
                    yield
        else:
            yield

    @contextmanager
    def ensure_open_text(self, node, inline=False):
        if node.annotations.get("requires_text"):
            with self.block_tag("mj-text", inline=inline):
                yield
        else:
            yield

    def visit_Document(self, node, scope):
        with self.block_tag("mjml"):
            if self.use_style:
                with self.block_tag("mj-head"):
                    with self.block_tag("mj-attributes"):
                        with self.block_tag(
                            "mj-section",
                            attrs={"padding": "0"},
                            self_closing=True,
                        ):
                            pass
            with self.block_tag("mj-body"):
                self.generic_visit(node, scope)

    def visit_Paragraph(self, node, scope):
        with self.ensure_open_column(node):
            self.generic_visit(node, scope)

    def visit_Heading(self, node, scope):
        with self.ensure_open_column(node):
            with self.ensure_open_text(node):
                with self.block_tag(f"h{node.level}", inline=True):
                    self.generic_visit(node, scope)

    def visit_BlockText(self, node, scope):
        with self.ensure_open_column(node):
            with self.ensure_open_text(node):
                self.generic_visit(node, scope)

    def visit_BlockQuote(self, node, scope):
        with self.ensure_open_column(node):
            with self.block_tag(
                "mj-text", attrs={"font-style": "italic", "color": "#555555"}
            ):
                self.generic_visit(node, scope)

    def visit_BlockCode(self, node, scope):
        with self.ensure_open_column(node):
            with self.ensure_open_text(node):
                with self.block_tag("pre"):
                    self.current.add_text(html.escape(node.code), indented=False)

    def visit_ThematicBreak(self, node, scope):
        with self.ensure_open_column(node):
            with self.block_tag(
                "mj-divider",
                attrs={"border-color": "#cccccc", "border-width": "1px"},
                self_closing=True,
            ):
                pass

    def visit_LineBreak(self, node, scope):
        self.current.add_text("<br/>")
        self.current.add_newline()

    def visit_SoftBreak(self, node, scope):
        self.current.add_text("<br/>")
        self.current.add_newline()

    def visit_BlankLine(self, node, scope):
        pass

    def visit_Image(self, node, scope):
        with self.ensure_open_column(node):
            attrs = {"src": node.url}
            if node.alt_text:
                attrs["alt"] = node.alt_text.value
            if node.title:
                attrs["title"] = node.title

            if node.annotations.get("requires_manual_image"):
                tag = "img"
                attrs["style"] = "max-width: 100%; height: auto;"
            else:
                tag = "mj-image"

            with self.block_tag(tag, attrs=attrs, self_closing=True):
                pass

    def visit_ImageLink(self, node, scope):
        with self.ensure_open_column(node):
            attrs = {"src": node.img.url, "href": node.href}
            if node.img.alt_text:
                attrs["alt"] = node.img.alt_text.value
            if node.img.title:
                attrs["title"] = node.img.title

            if node.img.annotations.get("requires_manual_image"):
                tag = "img"
                attrs["style"] = "max-width: 100%; height: auto;"
            else:
                tag = "mj-image"

            with self.block_tag(tag, attrs=attrs, self_closing=True, inline=True):
                pass

    def visit_List(self, node, scope):
        with self.ensure_open_column(node):
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
        with self.ensure_open_column(node):
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
        with self.block_tag("th", attrs=attrs, inline=True):
            self.generic_visit(node, scope)
        self.current.add_newline()

    def visit_TableCell(self, node, scope):
        attrs = {"align": node.align} if node.align else {}
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

    def visit_CodeSpan(self, node, scope):
        with self.ensure_open_text(node):
            with self.block_tag("code", inline=True):
                self.current.add_text(html.escape(node.code))
