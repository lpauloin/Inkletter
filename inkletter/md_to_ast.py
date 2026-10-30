from itertools import pairwise
from urllib.parse import quote

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from inkletter.ast import *
from inkletter.plugins import (
    bare_links_plugin,
    hashtag_plugin,
    link_attributes_plugin,
    task_lists_plugin,
    typed_lists_plugin,
)
from inkletter.theme import DEFAULT_THEME
from inkletter.visitors.annotation import Annotation
from inkletter.visitors.merger import BlockTextMerger
from inkletter.visitors.trimmer import Trimmer
from inkletter.visitors.urls import URLRewriter

# What a link's target keeps as it is: the delimiters of a URL (RFC 3986)
# and the octets already encoded; anything else — a space, an accented
# letter — is percent-encoded.
URL_SAFE = ":/?#@!$&()*+,;=%"

# What a node of an image's alt reads as, when it is not its own text.
ALT_SPELLINGS = {"softbreak": " ", "hardbreak": " ", "html_inline": ""}


# The containers whose blocks may have blank lines between them — and whose
# last block, not the container, says where it ends.
CONTAINERS = ("blockquote", "bullet_list", "ordered_list", "list_item")


class ASTBuilder:
    """Turns markdown-it's tree into Inkletter's.

    One method per kind of markdown-it node, named after it: each says what
    the node becomes, and calls `build` on what it holds. What the parser
    reads is markdown-it's business, and what a node means the passes'
    after this one: here, only shapes change.
    """

    # The target's scheme says what a link is: the node each one becomes,
    # and a plain Link for the rest — addresses, relative paths, whatever
    # else. The same idea as a visitor dispatching on a class: a scheme
    # added later gets its node here, once, rather than a test in every
    # visitor.
    LINKS_BY_SCHEME = {"urn": Mention, "mailto": MailLink, "tel": TelLink}
    # what a scheme names is a class of its own; anything else is an address
    DEFAULT_LINK = UrlLink

    def __init__(self, line_count):
        # the document's lines: the blank ones it ends on are counted too
        self.line_count = line_count

    def __call__(self, tree):
        return self.root(tree)

    def build(self, node):
        """What the node becomes: a node, or several where a container of
        markdown-it's is none of Inkletter's (a table's body, a line of
        text)."""
        return getattr(self, node.type)(node)

    def built(self, nodes):
        out = []
        for node in nodes:
            result = self.build(node)
            out.extend(result if isinstance(result, list) else [result])
        return out

    # --- Blank lines ---

    @classmethod
    def end_of(cls, node):
        """The line after a block's last: a container ends with what it
        holds — markdown-it counts in a list the blank lines that follow
        it, which are the document's."""
        if node.type in CONTAINERS and node.children:
            return cls.end_of(node.children[-1])
        if node.type == "list_item":
            return node.map[0] + 1
        return node.map[1]

    def blocks(self, children, start, end=None):
        """A container's blocks, with the blank lines its author left
        between them: from the line it starts on to the one it ends on,
        when that is known."""
        nodes, line = [], start
        for child in children:
            if child.map[0] > line:
                nodes.append(BlankLine(child.map[0] - line))
            nodes.extend(self.built([child]))
            line = self.end_of(child)
        if end is not None and end > line:
            nodes.append(BlankLine(end - line))
        return nodes

    # --- Blocks ---

    def root(self, node):
        return Document(self.blocks(node.children, 0, self.line_count))

    def paragraph(self, node):
        children = self.built(node.children)
        # a tight list's item holds its text, not a paragraph
        if node.nester_tokens.opening.hidden:
            return BlockText(children)
        return Paragraph(children)

    def heading(self, node):
        return Heading(int(node.tag[1:]), self.built(node.children))

    def blockquote(self, node):
        return BlockQuote(self.blocks(node.children, node.map[0]))

    def fence(self, node):
        return BlockCode(self.code_of(node), node.info.strip() or None)

    def code_block(self, node):
        return BlockCode(self.code_of(node), None)

    @staticmethod
    def code_of(node):
        # its lines, the break that ends the last one aside — fenced or
        # indented alike
        return node.content.removesuffix("\n")

    def html_block(self, node):
        return BlockHtml(node.content.strip("\n"))

    def hr(self, node):
        return ThematicBreak()

    # --- Lists ---

    def bullet_list(self, node):
        return List(self.built(node.children), ordered=False, gaps=self.gaps(node.children))

    def ordered_list(self, node):
        start = node.attrs.get("start")
        return List(
            self.built(node.children), ordered=True, start=start, gaps=self.gaps(node.children)
        )

    def gaps(self, items):
        """The blank lines between each item of a list and the next — none in
        a tight list, the author's own in a loose one."""
        return [after.map[0] - self.end_of(before) for before, after in pairwise(items)]

    def list_item(self, node):
        children = self.blocks(node.children, node.map[0])
        checked = node.meta.get("checked")
        if checked is None:
            return ListItem(children)
        return TaskListItem(children, checked)

    # --- Tables ---

    def table(self, node):
        header, *rows = self.built(node.children)
        return Table(header=header, rows=rows)

    def thead(self, node):
        (row,) = node.children
        return TableHeader(self.built(row.children))

    def tbody(self, node):
        return self.built(node.children)

    def tr(self, node):
        return TableRow(self.built(node.children))

    def th(self, node):
        return TableHeaderCell(self.built(node.children), align=self.align_of(node))

    def td(self, node):
        return TableCell(self.built(node.children), align=self.align_of(node))

    @staticmethod
    def align_of(node):
        style = node.attrs.get("style", "")
        return style.removeprefix("text-align:") or None

    # --- Inline ---

    def inline(self, node):
        return self.built(node.children)

    def text(self, node):
        # markdown-it leaves an empty text where a mark's delimiters were
        return [LiteralText(node.content)] if node.content else []

    def text_special(self, node):
        # an escaped character or an entity, read: in an image's alt, which
        # the parser does not join to the text around it
        return LiteralText(node.content)

    def hashtag(self, node):
        return Hashtag(node.meta["name"])

    def em(self, node):
        return Emphasis(self.built(node.children))

    def strong(self, node):
        return Strong(self.built(node.children))

    def s(self, node):
        return StrikeThrough(self.built(node.children))

    def code_inline(self, node):
        return CodeSpan(node.content)

    def html_inline(self, node):
        return InlineHtml(node.content)

    def softbreak(self, node):
        return SoftBreak()

    def hardbreak(self, node):
        return LineBreak()

    def link(self, node):
        url, title = node.attrs["href"], node.attrs.get("title")
        text = self.built(node.children)
        if runs_something(url):
            return text
        # What the target's scheme names — an entity, for a URN — becomes
        # its own node here, once, rather than being recognised again by
        # every visitor that walks past a link.
        kind = self.LINKS_BY_SCHEME.get(Link.scheme_of(url))
        if kind:
            return kind(text, url, title)
        # A link holding an image is the image, clickable: the rest of
        # its label is dropped
        image = next((child for child in text if isinstance(child, Image)), None)
        if image:
            return ImageLink(image, url, title)
        return self.DEFAULT_LINK(text, url, title)

    def image(self, node):
        if runs_something(node.attrs["src"]) and not IMAGE_DATA.match(node.attrs["src"]):
            return LiteralText(self.alt_text(node.children))
        return Image(
            node.attrs["src"],
            self.alt_text(node.children),
            node.attrs.get("title"),
            attributes=Attributes(**node.meta.get("ink_attributes", {})),
        )

    @classmethod
    def alt_text(cls, nodes):
        """What an image's alt reads as: its words, its code and its tags as
        written, a break as a space, its marks gone — an HTML alt holds no
        markup."""
        return "".join(cls.alt_part(node) for node in nodes)

    @classmethod
    def alt_part(cls, node):
        if node.type in ALT_SPELLINGS:
            return ALT_SPELLINGS[node.type]
        if node.type == "hashtag":
            return f"#{node.meta['name']}"
        if node.type in ("text", "text_special", "code_inline"):
            return node.content
        return cls.alt_text(node.children)


def create_markdown(link_attributes=True):
    """The parser: CommonMark, GitHub's tables and strikethrough, and what
    Inkletter reads beyond them."""
    markdown = MarkdownIt("commonmark").enable(["table", "strikethrough"])
    # Every target is read: what a link that runs something becomes is the
    # tree's to decide (`ASTBuilder.link`), and a URN must reach the mention
    # it names.
    markdown.validateLink = accept_any_link
    markdown.normalizeLink = normalize_link
    markdown.normalizeLinkText = str
    markdown.use(hashtag_plugin)
    # A bare address is text to CommonMark, and a link to every reader:
    # read as one, so the URL factory shortens it and the counter charges
    # it like any other.
    markdown.use(bare_links_plugin)
    markdown.use(task_lists_plugin)
    # A list ends where its author stopped writing it: a line written
    # after an item, without a marker, is its own block.
    markdown.use(typed_lists_plugin)
    if link_attributes:
        markdown.use(link_attributes_plugin)
    return markdown


def accept_any_link(url):
    return True


def normalize_link(url):
    """A link's target as the document holds it: written as typed, its
    entities and escapes already read, the rest percent-encoded."""
    return quote(url, safe=URL_SAFE)


def line_count(text):
    """How many lines markdown-it reads in a text: a last newline closes the
    last line rather than opening one."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def read_markdown(markdown_text, link_attributes=True):
    """The document as parsed, before any pass has said what it means."""
    tokens = create_markdown(link_attributes).parse(markdown_text)
    return ASTBuilder(line_count(markdown_text))(SyntaxTreeNode(tokens))


def parse_markdown_to_ast(
    markdown_text,
    bold_link_is_button=True,
    link_attributes=True,
    theme=None,
    url_factory=None,
):
    ast = read_markdown(markdown_text, link_attributes)
    # what is laid out on one line — a label, a name, a cell — is one
    Trimmer().visit(ast)

    if theme is None:
        theme = DEFAULT_THEME

    BlockTextMerger(bold_link_is_button=bold_link_is_button).visit(ast)
    Annotation(theme=theme, link_attributes=link_attributes).visit(ast)
    # Last, once every node says what it is: the factory is offered a
    # button's URL as a button's.
    if url_factory is not None:
        URLRewriter(url_factory).visit(ast)

    return ast
