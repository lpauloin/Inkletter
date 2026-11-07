import re
from html import escape

from inkletter.ast import *
from inkletter.lookalikes import strike
from inkletter.visitors.generic import NodeVisitor

# The attributes a caller may give a mention's anchor (`mentions`): a set
# breaking any rule is refused whole, and the mention goes out as `@name`.
#
# | Rule                                                  | Refused, e.g.          |
# |-------------------------------------------------------|------------------------|
# | a name is a letter, then letters, digits or `-`;      | `x onmouseover=y`,     |
# | written lower-cased, once                             | `xlink:href`           |
# | no event handler                                      | `onclick`              |
# | an address never runs something (`runs_something`)    | `href="javascript:…"`  |
# | a value is a string, escaped                          | `3`, `None`            |
ATTRIBUTE_NAME = re.compile(r"[a-z][a-z0-9-]*", re.IGNORECASE)
URL_ATTRIBUTES = ("href", "src", "action", "formaction")


def anchor_attributes(attributes):
    """The attributes of a mention's anchor as written in its tag, or None
    for `@name`: none given, none at all, or a set breaking a rule."""
    if not attributes:
        return None
    written = {}
    for key, value in attributes.items():
        if not isinstance(key, str) or not isinstance(value, str):
            return None
        name = key.lower()
        if not ATTRIBUTE_NAME.fullmatch(name) or name.startswith("on") or name in written:
            return None
        if name in URL_ATTRIBUTES and runs_something(value):
            return None
        written[name] = value
    return "".join(f' {name}="{escape(value)}"' for name, value in written.items())


class HtmlFragmentCodegen(NodeVisitor):
    """Renders the normalized AST as a fragment of HTML — the inside of a
    document, to be set inside another one: a report's note in a PDF, a
    preview on a screen.

    Sibling of the plain-text output. No theme applies: the page around
    the fragment styles it — of the annotations, only the hand-written
    anchors and a task's box are read. What it writes is safe to set
    inside a page that trusts nothing the author typed: every text is
    escaped, raw HTML — inline or block — is dropped, a target that runs
    something is never a link (`runs_something`), and an image is its
    alternative text: whatever renders the fragment never fetches
    anything for it — unless the caller asks for the pictures
    (`images=True`), for a page that serves them itself: then an image
    with a web address (`http`, `https`) or carried inside the page
    (`data:image/…`) is an `<img>`, one alone on its line a `<figure>`
    with its title as `<figcaption>`, and any other address stays its
    alternative text.

    For a page or an editor that wants them, three more, each asked for:

    | Option             | What the fragment writes                               |
    |--------------------|--------------------------------------------------------|
    | `mentions`         | each mention as an anchor with the attributes the      |
    |                    | caller's function gives for its URN — an address to a  |
    |                    | public page, an entity an editor reads back —, `@name` |
    |                    | when it gives none or a set the rules above refuse     |
    |                    | (`anchor_attributes`); without it, a mention is its    |
    |                    | name                                                   |
    | `unicode_strike`   | strikethrough in its Unicode look-alike, not `<s>`     |
    | `task_paragraphs`  | a list holding tasks as a paragraph per item, its box  |
    |                    | or its marker in its text, not a list                  |
    A hand-written anchor is a link, as a Markdown one,
    its tag rebuilt from its address alone. A line break the author typed
    stays one.
    """

    def __init__(self, images=False, mentions=None, unicode_strike=False, task_paragraphs=False):
        super().__init__()
        self.images = images
        # the attributes of a mention's anchor, by its URN, or None for `@name`
        self.mentions = mentions
        self.unicode_strike = unicode_strike
        self.task_paragraphs = task_paragraphs
        # inside a strikethrough written as its look-alike
        self.striking = False
        # the struck texts of the strikethrough being written, by the place
        # each holds in `parts`: struck once it closes, each space reading
        # its real neighbours across tags
        self.struck = []
        # what opens the first line of a list's item written as paragraphs
        self.marker = ""
        self.parts = []
        # Hand-written anchors opened and not closed yet: the block they sit
        # in closes them, whatever the author forgot.
        self.open_anchors = 0

    def get_html(self):
        return "".join(self.parts)

    def write(self, html):
        self.parts.append(html)

    def text(self, value):
        if self.striking and value:
            self.struck.append((len(self.parts), value))
        self.write(escape(value, quote=False))

    def wrapped(self, tag, node, scope, attributes=""):
        start = len(self.parts)
        self.write(f"<{tag}{attributes}>")
        self.line_opening(node)
        opened, self.open_anchors = self.open_anchors, 0
        self.generic_visit(node, scope)
        self.write("</a>" * self.open_anchors)
        self.open_anchors = opened
        if tag == "p" and "".join(self.parts[start + 1 :]) == "":
            # a paragraph with nothing to read — an image without its
            # alternative text — leaves nothing behind
            del self.parts[start:]
            return
        self.write(f"</{tag}>")

    # --- Blocks ---

    def visit_Document(self, node, scope):
        self.generic_visit(node, scope)

    def visit_Paragraph(self, node, scope):
        only = self.shown_alone(node)
        if only is not None:
            self.figure(only)
            return
        self.wrapped("p", node, scope)

    # --- Pictures, when asked for ---

    def shown(self, image):
        """Whether this image — or the one inside this link — is drawn,
        rather than said by its text (`Image.drawable`)."""
        return self.images and image.picture.drawable

    def shown_alone(self, node):
        """The one drawn image — linked or not — a paragraph holds and
        nothing else, or None."""
        if len(node.children) != 1:
            return None
        only = node.children[0]
        return only if isinstance(only, (Image, ImageLink)) and self.shown(only) else None

    def draw(self, image):
        self.write(f'<img src="{escape(image.url)}" alt="{escape(image.alt_text)}">')

    def figure(self, image):
        """A drawn image — or linked one — on its own line: laid small when
        its author said so, inside its link when it has one, its title
        under it."""
        picture = image.picture
        linked = isinstance(image, ImageLink)
        self.write(
            '<figure data-size="small">' if picture.attributes.size == "small" else "<figure>"
        )
        if linked:
            self.write(f'<a href="{escape(image.href)}">')
        self.draw(picture)
        if linked:
            self.write("</a>")
        if picture.title and picture.title.strip():
            self.write("<figcaption>")
            self.text(picture.title)
            self.write("</figcaption>")
        self.write("</figure>")

    def visit_BlockText(self, node, scope):
        # the text of a tight list's item: no paragraph of its own
        self.line_opening(node)
        self.generic_visit(node, scope)

    def line_opening(self, node):
        """What a line opens on: the marker of a list's item written as
        paragraphs, then the box of a task item's first line."""
        if self.marker:
            marker, self.marker = self.marker, ""
            self.text(marker)
        box = node.annotations.get("checkbox")
        if box:
            self.text(box + " ")

    def visit_Heading(self, node, scope):
        self.wrapped(f"h{node.level}", node, scope)

    def visit_BlockQuote(self, node, scope):
        self.wrapped("blockquote", node, scope)

    def visit_BlockCode(self, node, scope):
        self.write("<pre><code>")
        self.text(node.code or "")
        self.write("</code></pre>")

    def visit_ThematicBreak(self, node, scope):
        self.write("<hr>")

    def visit_BlankLine(self, node, scope):
        # between two blocks, the blocks themselves say it
        pass

    def visit_BlockHtml(self, node, scope):
        pass

    # --- Inline ---

    def visit_LiteralText(self, node, scope):
        self.text(node.value)

    def visit_CodeSpan(self, node, scope):
        # code stays as written, even inside a strikethrough
        self.write("<code>")
        self.write(escape(node.code, quote=False))
        self.write("</code>")

    def visit_Hashtag(self, node, scope):
        self.text(f"#{node.name}")

    def visit_InlineHtml(self, node, scope):
        # the tags vanish, the text between them stays — except an anchor,
        # rebuilt from its address alone
        if node.annotations.get("anchor_nested"):
            return
        href = node.annotations.get("anchor_opens")
        if href is not None:
            self.write(f'<a href="{escape(href)}">')
            self.open_anchors += 1
        elif node.annotations.get("anchor_href") and self.open_anchors:
            self.write("</a>")
            self.open_anchors -= 1

    def visit_Emphasis(self, node, scope):
        self.wrapped("em", node, scope)

    def visit_Strong(self, node, scope):
        self.wrapped("strong", node, scope)

    def visit_StrikeThrough(self, node, scope):
        if not self.unicode_strike:
            self.wrapped("s", node, scope)
            return
        if self.striking:
            self.generic_visit(node, scope)
            return
        self.striking = True
        self.generic_visit(node, scope)
        self.striking = False
        self.strike_written()

    def strike_written(self):
        """Each text of the strikethrough just written, struck in place, the
        texts around it read for the neighbours of its edges."""
        values = [value for _, value in self.struck]
        for at, (index, value) in enumerate(self.struck):
            before = values[at - 1] if at else ""
            after = values[at + 1] if at + 1 < len(values) else ""
            self.parts[index] = escape(strike(value, before, after), quote=False)
        self.struck = []

    def visit_UrlLink(self, node, scope):
        self.link(node, scope)

    def visit_MailLink(self, node, scope):
        self.link(node, scope)

    def visit_TelLink(self, node, scope):
        self.link(node, scope)

    def visit_Mention(self, node, scope):
        """Someone named: their name, never their URN. Asked for
        (`mentions`): a mention naming nobody writes nothing, one the caller
        gives no attributes for — or attributes the rules refuse
        (`anchor_attributes`) — goes out as `@name`, plain text, and any
        other is an anchor with those attributes — the name the author
        wrote, letters and case kept."""
        if self.mentions is None:
            self.generic_visit(node, scope)
            return
        name = node.plain_text()
        if not name:
            return
        written = anchor_attributes(self.mentions(node.urn))
        if written is None:
            self.text(f"@{name}")
            return
        self.write(f"<a{written}>")
        self.text(name)
        self.write("</a>")

    def link(self, node, scope):
        if all(child.is_blank() for child in node.children):
            # nothing to click on: the address is its own label
            self.write(f'<a href="{escape(node.href)}">')
            self.text(node.href)
            self.write("</a>")
            return
        self.wrapped("a", node, scope, f' href="{escape(node.href)}"')

    def visit_LineBreak(self, node, scope):
        self.write("<br>")

    def visit_SoftBreak(self, node, scope):
        self.write("<br>")

    # --- Images and layout conventions ---

    def visit_Image(self, node, scope):
        if self.shown(node):
            self.draw(node)
        elif node.says_something:
            self.text(node.alt_text)

    def visit_ImageLink(self, node, scope):
        if self.shown(node):
            self.write(f'<a href="{escape(node.href)}">')
            self.draw(node.img)
            self.write("</a>")
            return
        # its alternative text, as the link it was
        if node.says_something:
            self.write(f'<a href="{escape(node.href)}">')
            self.text(node.img.alt_text)
            self.write("</a>")

    def visit_ImageRow(self, node, scope):
        if any(self.shown(child) for child in node.children):
            # the pictures side by side, in one paragraph, apart as in the
            # source — and the text of those not drawn between them
            kept = [image for image in node.children if self.shown(image) or image.says_something]
            self.write("<p>")
            for index, image in enumerate(kept):
                if index:
                    self.write(" ")
                self.visit(image, scope)
            self.write("</p>")
            return
        # one line per image that says something, as the text output does
        alts = [image for image in node.children if image.says_something]
        if not alts:
            return
        self.write("<p>")
        for index, image in enumerate(alts):
            if index:
                self.write("<br>")
            self.visit(image, scope)
        self.write("</p>")

    def visit_MediaObject(self, node, scope):
        # the image — or its alternative text —, then the text beside it; a
        # linked one stays inside its link
        if self.shown(node.image):
            self.figure(node.image)
        elif node.image.says_something:
            self.write("<p>")
            self.visit(node.image, scope)
            self.write("</p>")
        self.write("<p>")
        for child in node.children:
            self.visit(child, scope)
        self.write("</p>")

    def visit_Button(self, node, scope):
        self.write(f'<p><a href="{escape(node.href)}"><strong>')
        self.generic_visit(node, scope)
        self.write("</strong></a></p>")

    # --- Lists ---

    def visit_List(self, node, scope):
        if self.task_paragraphs and any(isinstance(item, TaskListItem) for item in node.elements):
            first = 1 if node.start is None else node.start
            for number, item in enumerate(node.elements, start=first):
                marker = (
                    ""
                    if isinstance(item, TaskListItem)
                    else f"{number}. "
                    if node.ordered
                    else "• "
                )
                self.item_paragraphs(item, marker, scope)
            return
        tag = "ol" if node.ordered else "ul"
        start = f' start="{node.start}"' if node.ordered and node.start not in (None, 1) else ""
        self.write(f"<{tag}{start}>")
        self.generic_visit(node, scope)
        self.write(f"</{tag}>")

    def item_paragraphs(self, item, marker, scope):
        """A list's item as paragraphs, its marker — or its box — opening
        its first text, tight (`BlockText`) or loose (`Paragraph`)."""
        for at, block in enumerate(item.children):
            if at == 0 and isinstance(block, (BlockText, Paragraph)):
                self.marker = marker
            if isinstance(block, BlockText):
                self.write("<p>")
                self.visit(block, scope)
                self.write("</p>")
            else:
                self.visit(block, scope)
            self.marker = ""

    def visit_ListItem(self, node, scope):
        self.wrapped("li", node, scope)

    def visit_TaskListItem(self, node, scope):
        # the box stands for the marker, in a numbered list as in another
        self.wrapped("li", node, scope, ' style="list-style-type: none"')

    # --- Tables ---

    def visit_Table(self, node, scope):
        self.write("<table>")
        if node.header is not None:
            self.write("<thead>")
            self.visit(node.header, scope)
            self.write("</thead>")
        self.write("<tbody>")
        for row in node.rows or []:
            self.visit(row, scope)
        self.write("</tbody></table>")

    def visit_TableHeader(self, node, scope):
        self.write("<tr>")
        self.generic_visit(node, scope)
        self.write("</tr>")

    def visit_TableRow(self, node, scope):
        self.write("<tr>")
        self.generic_visit(node, scope)
        self.write("</tr>")

    def visit_TableCell(self, node, scope):
        self.cell("td", node, scope)

    def visit_TableHeaderCell(self, node, scope):
        self.cell("th", node, scope)

    def cell(self, tag, node, scope):
        align = (
            f' style="text-align: {node.align}"'
            if node.align in ("left", "center", "right")
            else ""
        )
        self.wrapped(tag, node, scope, align)
