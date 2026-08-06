from contextlib import contextmanager

from inkletter.ast import *
from inkletter.codeblock import (
    CodeBlock,
    CodeBlockResolver,
    Newline,
    TextElement,
)
from inkletter.visitors.generic import NodeVisitor

DIVIDER = "-" * 40


class TextCodegen(NodeVisitor):
    """Renders the normalized AST as the plain-text email alternative.

    Sibling of the MJML Codegen, built on the same CodeBlock machinery.
    Themes and annotations do not apply: plain text has no styling. A
    fragment that must be reshaped before landing in the output (quoted
    lines, padded table cells, an underline as wide as its title) is
    visited into a nested CodeBlock, resolved to text, transformed, then
    written to the current block.
    """

    def __init__(self):
        super().__init__()
        self.root = CodeBlock()
        self.resolver = CodeBlockResolver()
        self.current = self.root

    def get_text(self):
        text = self.resolver.resolve(self.root)
        return text + "\n" if text else ""

    def line(self, text=""):
        if text:
            self.current.add_text(text)
        self.current.add_newline()

    def close_line(self):
        """End the current line if the last element left it open."""
        for element in reversed(self.current.elements):
            if isinstance(element, (Newline, CodeBlock)):
                return  # nested blocks are always attached closed
            if isinstance(element, TextElement):
                self.current.add_newline()
                return

    def render_block(self, node, scope):
        """The node's output as its own CodeBlock, line closed."""
        with self.nested() as block:
            self.visit(node, scope)
            self.close_line()
        return block

    def emit_blocks(self, nodes, scope):
        """Emit the visible blocks separated by one blank line."""
        blocks = [self.render_block(node, scope) for node in nodes]
        visible = [block for block in blocks if block.elements]
        for index, block in enumerate(visible):
            if index:
                self.line()
            self.current.add_codeblock(block)

    @contextmanager
    def nested(self):
        """Divert the visit into a fresh CodeBlock, then restore."""
        parent, self.current = self.current, CodeBlock()
        yield self.current
        self.current = parent

    def resolve_inline(self, nodes, scope):
        """Flat text of inline nodes (labels, cells), via a nested block."""
        with self.nested() as block:
            for node in nodes:
                self.visit(node, scope)
        return self.resolver.resolve(block).strip()

    def visit_Document(self, node, scope):
        self.emit_blocks(node.children, scope)

    # --- Blocks ---

    def visit_Paragraph(self, node, scope):
        self.generic_visit(node, scope)

    def visit_BlockText(self, node, scope):
        self.generic_visit(node, scope)
        self.line()

    def visit_Heading(self, node, scope):
        with self.nested() as block:
            for child in node.children:
                self.visit(child, scope)
        title = self.resolver.resolve(block)
        for line in title.splitlines():
            self.line(line)
        width = max((len(line) for line in title.splitlines()), default=0)
        if node.level == 1 and width:
            self.line("=" * width)
        elif node.level == 2 and width:
            self.line("-" * width)

    def visit_BlockQuote(self, node, scope):
        with self.nested() as block:
            self.emit_blocks(node.children, scope)
        for line in self.resolver.resolve(block).splitlines():
            self.line(("> " + line).rstrip())

    def visit_BlockCode(self, node, scope):
        for line in node.code.splitlines():
            self.line("    " + line if line else "")

    def visit_ThematicBreak(self, node, scope):
        self.line(DIVIDER)

    def visit_BlankLine(self, node, scope):
        pass

    def visit_BlockHtml(self, node, scope):
        pass  # a raw HTML block has no reliable text rendering

    # --- Inline ---

    def visit_LiteralText(self, node, scope):
        self.current.add_text(node.value)

    def visit_CodeSpan(self, node, scope):
        self.current.add_text(node.code)

    def visit_InlineHtml(self, node, scope):
        pass  # the tags vanish, the surrounding text nodes remain

    def visit_TemplateTag(self, node, scope):
        # never escaped: Django reads the tag exactly as it was written
        self.current.add_text(node.raw)

    def visit_TemplateStatement(self, node, scope):
        self.line(node.raw)

    def visit_Emphasis(self, node, scope):
        self.generic_visit(node, scope)

    def visit_Strong(self, node, scope):
        self.generic_visit(node, scope)

    def visit_StrikeThrough(self, node, scope):
        self.generic_visit(node, scope)

    def visit_Link(self, node, scope):
        label = self.resolve_inline(node.children, scope)
        if not label or label == node.href:
            self.current.add_text(node.href)
        else:
            self.current.add_text(f"{label} <{node.href}>")

    def visit_LineBreak(self, node, scope):
        self.line()

    def visit_SoftBreak(self, node, scope):
        self.line()

    # --- Images and layout conventions ---

    def visit_Image(self, node, scope):
        alt = node.alt_text.value if node.alt_text else ""
        if alt:
            self.line(alt)

    def visit_ImageLink(self, node, scope):
        alt = node.img.alt_text.value if node.img.alt_text else ""
        if alt:
            self.line(f"{alt} <{node.href}>")
        else:
            self.line(node.href)

    def visit_ImageRow(self, node, scope):
        for image in node.children:
            self.visit(image, scope)

    def visit_MediaObject(self, node, scope):
        self.visit(node.image, scope)
        if self.current.elements:  # blank line only below a visible alt
            self.line()
        self.emit_blocks(node.children, scope)

    def visit_Button(self, node, scope):
        label = self.resolve_inline(node.children, scope).replace("\n", " ")
        self.line(f"→ {label.strip()} : {node.href}")

    # --- Lists ---

    def visit_List(self, node, scope):
        number = node.start if node.ordered and node.start else 1
        for item in node.elements:
            if isinstance(item, TaskListItem):
                marker = "[x] " if item.checked else "[ ] "
            elif node.ordered:
                marker = f"{number}. "
                number += 1
            else:
                marker = "- "
            self.current.add_text(marker)
            self.current.add_indent()
            for child in item.children:
                self.visit(child, scope)
            self.close_line()
            self.current.add_dedent()

    # --- Tables ---

    def cell_text(self, cell, scope):
        return self.resolve_inline(cell.children, scope).replace("\n", " ").strip()

    def visit_Table(self, node, scope):
        header = node.header.headers if node.header else []
        rows = [row.row for row in node.rows]
        aligns = [cell.align for cell in (header or (rows[0] if rows else []))]
        grid = [[self.cell_text(cell, scope) for cell in header]] if header else []
        grid += [[self.cell_text(cell, scope) for cell in row] for row in rows]
        if not grid:
            return
        columns = max(len(line) for line in grid)
        widths = [
            max(len(line[i]) if i < len(line) else 0 for line in grid)
            for i in range(columns)
        ]

        def pad(value, width, align):
            if align == "right":
                return value.rjust(width)
            if align == "center":
                return value.center(width)
            return value.ljust(width)

        def emit_row(line):
            padded = [
                pad(
                    line[i] if i < len(line) else "",
                    widths[i],
                    aligns[i] if i < len(aligns) else None,
                )
                for i in range(columns)
            ]
            self.line(" | ".join(padded).rstrip())

        if header:
            emit_row(grid[0])
            self.line("-+-".join("-" * width for width in widths))
            body = grid[1:]
        else:
            body = grid
        for line in body:
            emit_row(line)
