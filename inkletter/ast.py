from urllib.parse import urlsplit


class Node:
    def __init__(self):
        self.annotations = {}

    def get_children(self):
        return []

    def is_blank(self):
        """Nothing to read: a break, or text made of whitespace."""
        return False

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class BlockNode(Node):
    def __init__(self, children):
        super().__init__()
        if children is None:
            self.children = []
        else:
            self.children = children if isinstance(children, list) else [children]

    def get_children(self):
        return self.children


# --- Text elements ---


class Text(Node):
    pass


class TextBlock(Text, BlockNode):
    pass


class LiteralText(Text):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def is_blank(self):
        return not self.value.strip()

    def __repr__(self):
        return f"LiteralText('{self.value}')"


class CodeSpan(Text):
    def __init__(self, code):
        self.code = code
        super().__init__()

    def __repr__(self):
        return f"CodeSpan(code='{self.code}')"


class Hashtag(Text):
    """A `#tag` in the text: `#` at the start of a word, then letters, digits
    or underscores, one letter at least — so `#2026` is a number and `C#` a
    language, and a `# ` with its space is a heading long before the text is
    read. Its own node, read before any mark inside it could be one:
    `#équipe_rh` is one tag, not a name with an italic in it. The name is
    kept without the `#`, which each rendering writes."""

    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return f"Hashtag(name='{self.name}')"


class InlineHtml(Text):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"InlineHtml('{self.value}')"


class Emphasis(TextBlock):
    def __repr__(self):
        return "Emphasis()"


class Strong(TextBlock):
    @property
    def ask(self):
        """The one link this bold wraps, blanks aside — the call to action,
        which a lone bold link is — and None when it wraps anything else.
        A mention does not qualify: it names someone, it asks nothing."""
        inner = [child for child in self.children if not child.is_blank()]
        if len(inner) == 1 and isinstance(inner[0], Link) and not isinstance(inner[0], Mention):
            return inner[0]
        return None

    def __repr__(self):
        return "Strong()"


class StrikeThrough(TextBlock):
    def __repr__(self):
        return "StrikeThrough()"


class Link(TextBlock):
    """What a link is, whatever it points at: a label, a target, a title.
    Never a node of the tree itself — a target's scheme says which of the
    classes below it is, and a visitor names the one it renders."""

    def __init__(self, text, href, title=None):
        super().__init__(text)
        self.href = href
        self.title = title

    @staticmethod
    def scheme_of(target):
        """The scheme a target starts with, lower-cased — `https`,
        `mailto`, `urn` — and `""` for a path relative to nothing, or for
        a target the standard splitter refuses (an unclosed IPv6 bracket,
        say): what it is not, at least, is an address."""
        try:
            return urlsplit(target).scheme.lower()
        except ValueError:
            return ""

    # Each kind says its scheme; only an address has to read it off its
    # target, which may be `http`, `https` or none at all.
    scheme = None

    def __repr__(self):
        return f"{type(self).__name__}(href='{self.href}', title='{self.title}')"


class UrlLink(Link):
    """An address — `http`, `https`, or a path relative to one — that a
    reader follows and a factory may shorten."""

    @property
    def scheme(self):
        # read off the href each time: a factory may rewrite it
        return self.scheme_of(self.href)


class Mention(Link):
    """Someone named in the text, with the entity's URN as its target —
    `urn:li:organization:…`, `urn:li:person:…`: what the `urn` scheme
    names in a document is an entity to mention.

    A link by nature, and its own class so that each rendering says what
    it does with one — a marker on a feed, the name alone in a mail — and
    so that a URL factory, which is shown addresses alone, never replaces
    the URN with a dead one. Nor is a mention a call to action, however
    bold.

    The children carry the name as it is to be displayed — the one the
    destination matches on, case included — with no leading marker: the
    marker belongs to whichever rendering needs one.
    """

    scheme = "urn"

    @property
    def urn(self):
        return self.href

    def __repr__(self):
        return f"Mention(urn='{self.urn}')"


class MailLink(Link):
    """`mailto:` — an address to write to. A mail client draws it as any
    link; a feed, which has none, shows the address itself."""

    scheme = "mailto"

    @property
    def address(self):
        return urlsplit(self.href).path

    def __repr__(self):
        return f"MailLink(address='{self.address}')"


class TelLink(Link):
    """`tel:` — a number to call, shown as such where nothing can dial."""

    scheme = "tel"

    @property
    def number(self):
        return urlsplit(self.href).path

    def __repr__(self):
        return f"TelLink(number='{self.number}')"


# --- Block elements ---


class Document(BlockNode):
    def __repr__(self):
        return "Document()"


class Paragraph(BlockNode):
    def __repr__(self):
        return "Paragraph()"


class Heading(BlockNode):
    def __init__(self, level, text):
        super().__init__(text)
        self.level = level

    def __repr__(self):
        return f"Heading(level={self.level})"


class BlockText(BlockNode):
    def __repr__(self):
        return "BlockText()"


class BlockQuote(BlockNode):
    def __repr__(self):
        return "BlockQuote()"


class BlockCode(BlockNode):
    def __init__(self, code=None, language=None, children=None):
        super().__init__(children)
        self.code = code
        self.language = language

    def __repr__(self):
        return f"BlockCode(language='{self.language}', code='{self.code}')"


class BlockHtml(Node):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"BlockHtml('{self.value}')"


# --- Image element ---


class Attributes(Node):
    """What the author wrote in braces after an image.

    Facts about the asset, never appearance: the theme keeps deciding
    how images look. Not a child of the image — it describes it, it is
    not part of its content — so no visitor ever walks into it.
    """

    def __init__(self, width=None, height=None, align=None):
        super().__init__()
        self.width = width
        self.height = height
        self.align = align

    def __bool__(self):
        return bool(self.width or self.height or self.align)

    def __repr__(self):
        return f"Attributes(width='{self.width}', height='{self.height}', align='{self.align}')"


class Image(Node):
    def __init__(self, url, alt_text=None, title=None, attributes=None):
        super().__init__()
        self.url = url
        self.alt_text = alt_text
        self.title = title
        self.attributes = attributes if attributes is not None else Attributes()

    @property
    def scheme(self):
        return Link.scheme_of(self.url)

    def get_children(self):
        if self.alt_text is None:
            return []
        if isinstance(self.alt_text, list):
            return self.alt_text
        return [self.alt_text]

    def __repr__(self):
        return f"Image(url='{self.url}', title='{self.title}', alt_text='{self.alt_text}'"


class ImageLink(Node):
    def __init__(self, img, href, title=None):
        super().__init__()
        self.img = img
        self.href = href
        self.title = title

    @property
    def scheme(self):
        return Link.scheme_of(self.href)

    def get_children(self):
        return [self.img]

    def __repr__(self):
        return f"ImageLink(href='{self.href}', img='{self.img}', title='{self.title}')"


class ImageRow(BlockNode):
    """A paragraph made only of images: rendered as side-by-side columns."""

    def __repr__(self):
        return "ImageRow()"


class Button(BlockNode):
    """A paragraph made only of a bold link: a call-to-action button.

    `children` is the inline label content of the link.
    """

    def __init__(self, children, href, title=None):
        super().__init__(children)
        self.href = href
        self.title = title

    @property
    def scheme(self):
        return Link.scheme_of(self.href)

    def __repr__(self):
        return f"Button(href='{self.href}', title='{self.title}')"


class MediaObject(BlockNode):
    """A paragraph opening (or closing) with a single image beside its text.

    `side` records where the image sits in the source paragraph.
    """

    def __init__(self, image, children, side="left"):
        super().__init__(children)
        self.image = image
        self.side = side

    def get_children(self):
        return [self.image] + self.children

    def __repr__(self):
        return f"MediaObject(side='{self.side}')"


# --- Terminal elements ---


class Terminal(Node):
    pass


class TextTerminal(Text, Terminal):
    def is_blank(self):
        return True

    pass


class ThematicBreak(Terminal):
    def __repr__(self):
        return "ThematicBreak()"


class LineBreak(TextTerminal):
    def __repr__(self):
        return "LineBreak()"


class SoftBreak(TextTerminal):
    def __repr__(self):
        return "SoftBreak()"


class BlankLine(TextTerminal):
    def __repr__(self):
        return "BlankLine()"


# --- List elements ---


class List(Node):
    def __init__(self, elements, ordered=False, start=None):
        super().__init__()
        self.elements = elements
        self.ordered = ordered
        self.start = start

    def get_children(self):
        return self.elements

    def __repr__(self):
        return f"List(ordered={self.ordered}, start={self.start})"


class ListItem(BlockNode):
    def __init__(self, children):
        super().__init__(children)

    def __repr__(self):
        return "ListItem()"


class TaskListItem(BlockNode):
    def __init__(self, children, checked=False):
        super().__init__(children)
        self.checked = checked

    def __repr__(self):
        return f"TaskListItem(checked={self.checked})"


# --- Table elements ---


class Table(Node):
    def __init__(self, header=None, rows=None):
        super().__init__()
        self.header = header
        self.rows = rows

    def get_children(self):
        header = [self.header] if self.header is not None else []
        return header + (self.rows or [])

    def __repr__(self):
        return "Table()"


class TableRow(Node):
    def __init__(self, row, is_header=False):
        super().__init__()
        self.row = row
        self.is_header = is_header

    def get_children(self):
        return self.row

    def __repr__(self):
        return f"TableRow(is_header={self.is_header})"


class TableCell(BlockNode):
    def __init__(self, cell, align=None):
        super().__init__(cell)
        self.align = align


class TableHeaderCell(TableCell):
    def __repr__(self):
        return f"TableHeaderCell(align={self.align})"


class TableHeader(Node):
    def __init__(self, headers):
        super().__init__()
        self.headers = headers

    def get_children(self):
        return self.headers

    def __repr__(self):
        return "TableHeader()"
