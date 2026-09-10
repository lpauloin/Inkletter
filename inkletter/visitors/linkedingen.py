"""Renders the normalized AST as a LinkedIn post.

The plain-text output, with a feed's choices: the platform has no
formatting, no columns, no buttons — the tree is built without any — and
draws no rule, which becomes the blank line between two blocks. Every
line comes from the same machinery as the mail's text alternative; what
differs is written here, and nothing else.

What this output adds is the **price**: every fragment it writes carries
what the platform will count for it. Almost every fragment costs its own
characters, measured in the platform's unit; a mention's marker costs the
name it displays, and an address on its way to a shortener costs the
short link it will become. The price is fixed when the fragment is
written, and the resolver that lays the lines out sums it as it goes.

Images are not supported — a post carries its visual beside the text,
never inside it — so one written in the document stays as it was written.
The tree arrives trimmed (`Trimmer`, a pass of `parse_markdown_to_ast`):
whatever is laid out on one line — a label, a name, a cell — already is.
"""

from string import ascii_letters

from inkletter.ast import *
from inkletter.codeblock import CodeBlockResolver
from inkletter.counting import cost_of_link, cost_of_mention, cost_of_text
from inkletter.visitors.textgen import TextCodegen
from inkletter.visitors.urls import REWRITABLE_SCHEMES

BULLET = "• "
CELL_SEPARATOR = " — "
LABEL_SEPARATOR = " : "

# The delimiters of the mention marker, for which nothing documents an
# escape. A display name carrying either cannot be expressed as a mention
# at all, and goes out as plain text rather than as a marker cut in half.
MARKER_DELIMITERS = ("|", "]")

# Unicode look-alikes for the three styles the platform does not have. They
# are text, not formatting: a screen reader spells them out letter by
# letter and the platform's search does not match them, which is why they
# are opt-in rather than a default.
BOLD = str.maketrans(
    ascii_letters, "".join(map(chr, [*range(0x1D5EE, 0x1D608), *range(0x1D5D4, 0x1D5EE)]))
)
ITALIC = str.maketrans(
    ascii_letters, "".join(map(chr, [*range(0x1D622, 0x1D63C), *range(0x1D608, 0x1D622)]))
)
STRIKE = "̶"
STYLES = {
    "bold": lambda text: text.translate(BOLD),
    "italic": lambda text: text.translate(ITALIC),
    "strikethrough": lambda text: "".join(c + STRIKE for c in text),
}


class LinkedinCodegen(TextCodegen):
    @classmethod
    def plain_text(cls, node):
        """What a node reads as, with no rendering: enough to tell a label
        that is an address from one that is words."""
        if isinstance(node, LiteralText):
            return node.value
        if isinstance(node, CodeSpan):
            return node.code
        return "".join(cls.plain_text(child) for child in node.get_children())

    def __init__(self, *, unicode_styling=False, link_length=None):
        super().__init__(bullet=BULLET)
        self.resolver = CodeBlockResolver(measure=cost_of_text)
        self.unicode_styling = unicode_styling
        self.link_length = link_length
        self.styles = []  # the styles in force around what is written

    def write(self, text, cost=None):
        """Plain text takes the styles in force, when substitutes are
        wanted, and costs what it says; what is priced — a marker, an
        address — is left alone, or it would stop resolving."""
        if cost is None and self.unicode_styling:
            for style in self.styles:
                text = STYLES[style](text)
        self.current.add_text(text, cost=cost)

    def write_link(self, url):
        """The address in full — readable, and the one thing an author can
        check — priced at the short link it will become, when the factory
        says what width it produces."""
        self.write(url, cost_of_link(url, self.link_length))

    def render(self, document):
        """The text, and what the platform will count for it. Trailing
        whitespace goes, as the platform trims it before it counts."""
        self.visit(document)
        return self.resolver.resolve(self.root).rstrip(), self.resolver.length

    # --- Blocks ---

    def visit_Heading(self, node, scope):
        """The text on its line, and no underline: a row of equals signs is
        a convention of plain-text mail, not of a feed."""
        self.generic_visit(node, scope)
        self.close_line()

    def visit_ThematicBreak(self, node, scope):
        pass  # forty dashes across a feed are noise; the blank line stays

    def visit_Table(self, node, scope):
        """One line per row, cells joined by a dash: a proportional font
        undoes any alignment, so padded columns would arrive ragged."""
        rows = ([node.header.headers] if node.header else []) + [row.row for row in node.rows]
        for row in rows:
            for index, cell in enumerate(cell for cell in row if cell.children):
                if index:
                    self.write(CELL_SEPARATOR)
                self.generic_visit(cell, scope)
            self.close_line()

    # --- Inline ---

    def visit_InlineHtml(self, node, scope):
        # the tags vanish, the surrounding text remains — except a closing
        # anchor, which spells out the address its opening tag carried,
        # exactly as a Markdown link does
        href = node.annotations.get("anchor_href")
        if href:
            self.write(LABEL_SEPARATOR)
            self.write_link(href)

    def visit_Mention(self, node, scope):
        """`@[<urn>|<name>]`, the one form a publishing API resolves into a
        real mention. The name is the author's and travels verbatim; the
        marker is the API's, and the platform weighs the name alone. A
        name the marker cannot carry goes out as plain text."""
        name = self.plain_text(node)
        if any(delimiter in name for delimiter in MARKER_DELIMITERS):
            return self.write(f"@{name}")
        self.write(f"@[{node.urn}|{name}]", cost_of_mention(name))

    def visit_Link(self, node, scope):
        """`label : url`, and the url alone when the label is one too — a
        bare address the author typed, which the parser encapsulates and a
        factory may have shortened since, so the two halves no longer
        match. No angle brackets either: a feed shows them, it does not
        read them."""
        label = self.plain_text(node)
        if label and label != node.href and not label.startswith(REWRITABLE_SCHEMES):
            self.generic_visit(node, scope)
            self.write(LABEL_SEPARATOR)
        self.write_link(node.href)

    def styled(self, node, scope, style):
        """The platform shows no formatting, so the choice is between losing
        it and paying for a look-alike that costs two units a letter and
        reads as gibberish aloud: the style is put in force around the
        children, and `write` applies it to plain text only."""
        self.styles.append(style)
        self.generic_visit(node, scope)
        self.styles.pop()

    def visit_Strong(self, node, scope):
        self.styled(node, scope, "bold")

    def visit_Emphasis(self, node, scope):
        self.styled(node, scope, "italic")

    def visit_StrikeThrough(self, node, scope):
        self.styled(node, scope, "strikethrough")

    # --- Images are not supported: written, they stay as written ---

    def visit_Image(self, node, scope):
        alt = node.alt_text.value if node.alt_text else ""
        self.write(f"![{alt}]({node.url})")

    def visit_ImageLink(self, node, scope):
        alt = node.img.alt_text.value if node.img.alt_text else ""
        self.write(f"[![{alt}]({node.img.url})]({node.href})")
        self.close_line()

    def visit_MediaObject(self, node, scope):
        # the image beside its text, as written: a block, then the others
        self.emit_blocks([node.image, *node.children], scope)
