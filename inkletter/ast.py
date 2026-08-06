class Node:
    def __init__(self):
        self.annotations = {}

    def get_children(self):
        return []

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

    def __repr__(self):
        return f"LiteralText('{self.value}')"


class CodeSpan(Text):
    def __init__(self, code):
        self.code = code
        super().__init__()

    def __repr__(self):
        return f"CodeSpan(code='{self.code}')"


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
    def __repr__(self):
        return "Strong()"


class StrikeThrough(TextBlock):
    def __repr__(self):
        return "StrikeThrough()"


class Link(TextBlock):
    def __init__(self, text, href, title=None):
        super().__init__(text)
        self.href = href
        self.title = title

    def __repr__(self):
        return f"Link(href='{self.href}', title='{self.title}')"


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


class Image(Node):
    def __init__(self, url, alt_text=None, title=None):
        super().__init__()
        self.url = url
        self.alt_text = alt_text
        self.title = title

    def get_children(self):
        if self.alt_text is None:
            return []
        if isinstance(self.alt_text, list):
            return self.alt_text
        return [self.alt_text]

    def __repr__(self):
        return (
            f"Image(url='{self.url}', title='{self.title}', alt_text='{self.alt_text}'"
        )


class ImageLink(Node):
    def __init__(self, img, href, title=None):
        super().__init__()
        self.img = img
        self.href = href
        self.title = title

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
        if self.header is None:
            if self.rows is None:
                children = []
            else:
                children = self.rows
        else:
            children = [self.header] + self.rows
        return children

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


class TableRegularCell(TableCell):
    def __repr__(self):
        return f"TableRegularCell(align={self.align})"


class TableHeader(Node):
    def __init__(self, headers):
        super().__init__()
        self.headers = headers

    def get_children(self):
        return self.headers

    def __repr__(self):
        return "TableHeader()"
