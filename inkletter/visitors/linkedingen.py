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

import unicodedata
from string import ascii_letters

from inkletter.ast import *
from inkletter.codeblock import CodeBlockResolver
from inkletter.counting import cost_of_link, cost_of_mention, cost_of_text
from inkletter.visitors.textgen import TextCodegen

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
#
# | Styles in force  | Letters become                           |
# |------------------|------------------------------------------|
# | bold             | 𝗺𝗼𝘁 sans-serif bold                       |
# | italic           | 𝘮𝘰𝘵 sans-serif italic                     |
# | bold and italic  | 𝙢𝙤𝙩 sans-serif bold italic — one table,   |
# |                  | whichever is outside: a second table     |
# |                  | would find no ASCII letter left to map   |
# | strikethrough    | a combining stroke after each letter,    |
# |                  | digit, sign or space — never an emoji —  |
# |                  | on top of the letters' own look-alike    |
#
# Only unaccented ASCII letters have a look-alike; accents and digits stay
# as they are.


def lookalikes(lower, upper):
    return str.maketrans(
        ascii_letters, "".join(map(chr, [*range(lower, lower + 26), *range(upper, upper + 26)]))
    )


LETTERS = {
    frozenset({"bold"}): lookalikes(0x1D5EE, 0x1D5D4),
    frozenset({"italic"}): lookalikes(0x1D622, 0x1D608),
    frozenset({"bold", "italic"}): lookalikes(0x1D656, 0x1D63C),
}
STRIKE = "\u0336"
# What the stroke goes after: letters, digits, punctuation, spaces and the
# like. Not an emoji, nor what an emoji is built of — a joiner, a variation
# selector, a skin tone — where a stroke breaks the picture instead of
# crossing it out.
STRUCK_CATEGORIES = ("L", "N", "P", "Zs", "Sc", "Sm")


def strike(text):
    return "".join(
        char + STRIKE if unicodedata.category(char).startswith(STRUCK_CATEGORIES) else char
        for char in text
    )


def substitute(text, styles):
    """`text` in the look-alikes of `styles`."""
    letters = LETTERS.get(frozenset(styles) & {"bold", "italic"})
    if letters:
        text = text.translate(letters)
    if "strikethrough" in styles:
        text = strike(text)
    return text


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

    def write(self, text, cost=None):
        """Text costs what it says, unless it is priced — a marker, an
        address."""
        self.current.add_text(text, cost=cost)

    def write_styled(self, text, annotations):
        """The author's words, in the look-alikes of the styles the
        annotation says are in force around them, when substitutes are
        wanted. Only words: a marker or an address is never styled, or it
        would stop resolving."""
        styles = annotations.get("styles")
        if self.unicode_styling and styles:
            text = substitute(text, styles)
        self.write(text)

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

    def visit_UrlLink(self, node, scope):
        """`label : url`, and the url alone when the label is one too — a
        bare address the author typed, which the parser encapsulates and a
        factory may have shortened since, so the two halves no longer
        match. No angle brackets either: a feed shows them, it does not
        read them."""
        label = self.plain_text(node)
        if label and label != node.href and Link.scheme_of(label) not in ("http", "https"):
            self.generic_visit(node, scope)
            self.write(LABEL_SEPARATOR)
        self.write_link(node.href)

    def visit_MailLink(self, node, scope):
        self.named(node, node.address, scope)

    def visit_TelLink(self, node, scope):
        self.named(node, node.number, scope)

    def named(self, node, target, scope):
        """`label : target`, and the target alone when the label is it, or
        the whole `mailto:`/`tel:` the parser wrote for a bare one — a feed
        dials nothing and drafts nothing, so what it shows is the address
        or the number, as words."""
        label = self.plain_text(node)
        if label and label not in (target, node.href):
            self.generic_visit(node, scope)
            self.write(LABEL_SEPARATOR)
        self.write(target)

    def visit_LiteralText(self, node, scope):
        self.write_styled(node.value, node.annotations)

    def visit_Hashtag(self, node, scope):
        # As written, whatever style is in force: in look-alikes it would be
        # another tag than the author's.
        self.write(f"#{node.name}")

    def visit_CodeSpan(self, node, scope):
        self.write_styled(node.code, node.annotations)

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
