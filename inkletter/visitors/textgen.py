from contextlib import contextmanager

from inkletter.ast import *
from inkletter.codeblock import (
    CodeBlock,
    CodeBlockResolver,
    Newline,
    TextElement,
)
from inkletter.plugins.bare_domains import is_spelled_by
from inkletter.visitors.generic import NodeVisitor

DIVIDER = "-" * 40
BULLET = "- "


class TextCodegen(NodeVisitor):
    """Renders the normalized AST as the plain-text email alternative.

    Sibling of the MJML Codegen, built on the same CodeBlock machinery,
    and the base of the LinkedIn output, which keeps its lines and
    changes its choices. Themes and styles do not apply: plain text has no
    styling; of the annotations, it reads what the document says — an
    item's rank, a hand-written anchor, a label that is an address. A
    fragment that needs a width before landing in the output (padded table
    cells, an underline as wide as its title) is visited into a nested
    CodeBlock, resolved to text, shaped, then written to the current block;
    a quote needs none, its marker being a line prefix the resolver puts
    there.
    """

    def __init__(self, bullet=BULLET):
        super().__init__()
        self.bullet = bullet
        self.root = CodeBlock()
        self.resolver = CodeBlockResolver()
        self.current = self.root

    def get_text(self):
        text = self.resolver.resolve(self.root)
        return text + "\n" if text else ""

    def write(self, text):
        """Every piece of text goes through here, so that an output built
        on this one can say something about what it writes."""
        self.current.add_text(text)

    def line(self, text=""):
        if text:
            self.write(text)
        self.current.add_newline()

    def line_open(self):
        """Whether the last element left the current line open."""
        for element in reversed(self.current.elements):
            if isinstance(element, (Newline, CodeBlock)):
                return False  # nested blocks are always attached closed
            if isinstance(element, TextElement):
                return True
        return False

    def close_line(self):
        """End the current line if the last element left it open."""
        if self.line_open():
            self.current.add_newline()

    def render_block(self, node, scope):
        """The node's output as its own CodeBlock, line closed."""
        with self.nested() as block:
            self.visit(node, scope)
            self.close_line()
        return block

    def emit_blocks(self, nodes, scope):
        """Emit the visible blocks separated by one blank line."""
        written = False
        for node in nodes:
            if not written and self.line_open():
                # the first block continues a line already open — an item's
                # marker, a quote's — and writes what it opens with there
                if self.wrote(node, scope):
                    self.close_line()
                    written = True
                continue
            block = self.render_block(node, scope)
            if not shows_text(block.elements):
                continue
            if written:
                self.line()
            self.current.add_codeblock(block)
            written = True
        return written

    def wrote(self, node, scope):
        """Visit a node where the writing stands; whether it wrote words. What
        a visit that wrote none left — a break, an indent, a quote's mark — is
        taken back, the line kept for what comes next."""
        before = len(self.current.elements)
        self.visit(node, scope)
        if shows_text(self.current.elements[before:]):
            return True
        del self.current.elements[before:]
        return False

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
        self.close_line()

    def visit_BlockText(self, node, scope):
        # a run of a line: whoever holds it ends the line
        self.generic_visit(node, scope)

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
        # the marker is a prefix on every line of the quote, blank ones
        # included — the resolver puts it there, no string goes round; on a
        # line already open (an item's marker), it is written there
        before = len(self.current.elements)
        if self.line_open():
            self.write("> ")
        self.current.add_indent("> ")
        written = self.emit_blocks(node.children, scope)
        self.current.add_dedent()
        if not written:
            # a quote of nothing leaves no mark
            del self.current.elements[before:]

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
        self.write(node.value)

    def visit_CodeSpan(self, node, scope):
        self.write(node.code)

    def visit_Hashtag(self, node, scope):
        self.write(f"#{node.name}")

    def visit_InlineHtml(self, node, scope):
        # the tags vanish, the surrounding text nodes remain — except a
        # closing anchor, which spells out the URL its opening tag
        # carried, exactly as a Markdown link does
        href = node.annotations.get("anchor_href")
        if href:
            self.write(f" <{href}>")

    def visit_Emphasis(self, node, scope):
        self.generic_visit(node, scope)

    def visit_Strong(self, node, scope):
        self.generic_visit(node, scope)

    def visit_StrikeThrough(self, node, scope):
        self.generic_visit(node, scope)

    def visit_UrlLink(self, node, scope):
        # The label beside the address unless it spells it: compared once
        # a factory has rewritten the address, so a shortened link still
        # says, in words, where it leads.
        label = self.resolve_inline(node.children, scope)
        if not label or is_spelled_by(node.href, label):
            self.write(node.href)
        else:
            self.write(f"{label} <{node.href}>")

    def visit_MailLink(self, node, scope):
        self.named(node, node.address, scope)

    def visit_TelLink(self, node, scope):
        self.named(node, node.number, scope)

    def named(self, node, target, scope):
        # the address or the number alone when the label is it — a bare
        # `<bonjour@exemple.fr>` — rather than twice, once with its scheme
        if node.annotations["label_is_address"]:
            self.write(target)
        else:
            self.write(f"{self.resolve_inline(node.children, scope)} <{node.href}>")

    def visit_LineBreak(self, node, scope):
        self.line()

    def visit_SoftBreak(self, node, scope):
        self.line()

    # --- Images and layout conventions ---

    def visit_Image(self, node, scope):
        if node.says_something:
            self.write(node.alt_text)

    def visit_ImageLink(self, node, scope):
        if node.says_something:
            self.write(f"{node.img.alt_text} <{node.href}>")
        else:
            self.write(node.href)

    def visit_ImageRow(self, node, scope):
        # one line per image
        for image in node.children:
            self.visit(image, scope)
            self.close_line()

    def visit_MediaObject(self, node, scope):
        self.visit(node.image, scope)
        if self.current.elements:  # blank line only below a visible alt
            self.close_line()
            self.line()
        self.emit_blocks(node.children, scope)

    def visit_Button(self, node, scope):
        label = self.resolve_inline(node.children, scope).replace("\n", " ").strip()
        # a bare address made a button reads as the address, once
        self.line(
            f"→ {node.href}" if is_spelled_by(node.href, label) else f"→ {label} : {node.href}"
        )

    # --- Lists ---

    def blank_lines_before(self, node, index):
        """The blank lines written before an item: in a text, none — a list
        reads as one block, loose or tight."""
        return 0

    def visit_List(self, node, scope):
        for index, item in enumerate(node.elements):
            for _ in range(self.blank_lines_before(node, index)):
                self.line()
            self.visit(item, scope)

    def visit_ListItem(self, node, scope):
        number = node.annotations.get("number")
        self.item(node, self.bullet if number is None else f"{number}. ", scope)

    def visit_TaskListItem(self, node, scope):
        self.item(node, "[x] " if node.checked else "[ ] ", scope)

    def item(self, node, marker, scope):
        """An item on its marker, what it holds indented under it."""
        self.write(marker)
        self.current.add_indent()
        for child in node.children:
            # a block that writes nothing leaves the line to the next one
            if self.wrote(child, scope):
                self.close_line()
        # an empty item still ends on its marker's line
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
            max(len(line[i]) if i < len(line) else 0 for line in grid) for i in range(columns)
        ]
        if header:
            self.row(grid[0], widths, aligns)
            self.line("-+-".join("-" * width for width in widths))
            body = grid[1:]
        else:
            body = grid
        for line in body:
            self.row(line, widths, aligns)

    def row(self, line, widths, aligns):
        """One line of a table, each cell padded to its column."""
        padded = [
            pad(
                line[i] if i < len(line) else "",
                width,
                aligns[i] if i < len(aligns) else None,
            )
            for i, width in enumerate(widths)
        ]
        self.line(" | ".join(padded).rstrip())


def pad(value, width, align):
    """A cell's text at its column's width, on the side its alignment says."""
    if align == "right":
        return value.rjust(width)
    if align == "center":
        return value.center(width)
    return value.ljust(width)


def shows_text(elements):
    """Whether elements hold words a reader sees, nested blocks included."""
    for element in elements:
        if isinstance(element, TextElement) and element.text.strip():
            return True
        if isinstance(element, CodeBlock) and shows_text(element.elements):
            return True
    return False
