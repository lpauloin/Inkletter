from html import escape

from inkletter.ast import *
from inkletter.visitors.generic import NodeVisitor

# The schemes a fragment links to; any other target is written as its label.
LINKED_SCHEMES = ("", "http", "https", "mailto", "tel")


class HtmlFragmentCodegen(NodeVisitor):
    """Renders the normalized AST as a fragment of HTML — the inside of a
    document, to be set inside another one: a report's note in a PDF, a
    preview on a screen.

    Sibling of the plain-text output. No theme applies: the page around
    the fragment styles it — of the annotations, only the hand-written
    anchors are read. What it writes is safe to set
    inside a page that trusts nothing the author typed: every text is
    escaped, raw HTML — inline or block — is dropped, a link to any scheme
    but those of `LINKED_SCHEMES` is written as its label, and an image is
    its alternative text: whatever renders the fragment never fetches
    anything for it. A hand-written anchor is a link, as a Markdown one,
    its tag rebuilt from its address alone. A line break the author typed
    stays one, as a post keeps it.
    """

    def __init__(self):
        super().__init__()
        self.parts = []
        # Hand-written anchors opened and not closed yet, each saying
        # whether its tag was written — a scheme the fragment does not
        # link to opens none: the block they sit in closes them, whatever
        # the author forgot.
        self.open_anchors = []

    def get_html(self):
        return "".join(self.parts)

    def write(self, html):
        self.parts.append(html)

    def text(self, value):
        self.write(escape(value, quote=False))

    def wrapped(self, tag, node, scope, attributes=""):
        start = len(self.parts)
        self.write(f"<{tag}{attributes}>")
        opened, self.open_anchors = self.open_anchors, []
        self.generic_visit(node, scope)
        self.write("</a>" * self.open_anchors.count(True))
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
        self.wrapped("p", node, scope)

    def visit_BlockText(self, node, scope):
        # the text of a tight list's item: no paragraph of its own
        self.generic_visit(node, scope)

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
        self.write("<code>")
        self.text(node.code)
        self.write("</code>")

    def visit_Hashtag(self, node, scope):
        self.text(f"#{node.name}")

    def visit_InlineHtml(self, node, scope):
        # the tags vanish, the text between them stays — except an anchor,
        # rebuilt from its address alone
        href = node.annotations.get("anchor_opens")
        if href is not None:
            linked = Link.scheme_of(href) in LINKED_SCHEMES
            if linked:
                self.write(f'<a href="{escape(href)}">')
            self.open_anchors.append(linked)
        elif node.annotations.get("anchor_href") and self.open_anchors:
            if self.open_anchors.pop():
                self.write("</a>")

    def visit_Emphasis(self, node, scope):
        self.wrapped("em", node, scope)

    def visit_Strong(self, node, scope):
        self.wrapped("strong", node, scope)

    def visit_StrikeThrough(self, node, scope):
        self.wrapped("s", node, scope)

    def visit_UrlLink(self, node, scope):
        self.link(node, scope)

    def visit_MailLink(self, node, scope):
        self.link(node, scope)

    def visit_TelLink(self, node, scope):
        self.link(node, scope)

    def visit_Mention(self, node, scope):
        # someone named: their name, never their URN
        self.generic_visit(node, scope)

    def link(self, node, scope):
        if node.scheme not in LINKED_SCHEMES:
            self.generic_visit(node, scope)
            return
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
        if self.alt_of(node):
            self.text(node.alt_text)

    def visit_ImageLink(self, node, scope):
        self.visit(node.img, scope)

    def visit_ImageRow(self, node, scope):
        # one line per image that says something, as the text output does
        alts = [image for image in node.children if self.alt_of(image)]
        if not alts:
            return
        self.write("<p>")
        for index, image in enumerate(alts):
            if index:
                self.write("<br>")
            self.visit(image, scope)
        self.write("</p>")

    def visit_MediaObject(self, node, scope):
        # the image's alternative text, then the text beside it
        if self.alt_of(node.image):
            self.write("<p>")
            self.visit(node.image, scope)
            self.write("</p>")
        self.write("<p>")
        for child in node.children:
            self.visit(child, scope)
        self.write("</p>")

    @staticmethod
    def alt_of(image):
        """Whether an image, linked or not, has an alternative text to show."""
        image = image.img if isinstance(image, ImageLink) else image
        return bool(image.alt_text.strip())

    def visit_Button(self, node, scope):
        if Link.scheme_of(node.href) not in LINKED_SCHEMES:
            self.wrapped("p", node, scope)
            return
        self.write(f'<p><a href="{escape(node.href)}"><strong>')
        self.generic_visit(node, scope)
        self.write("</strong></a></p>")

    # --- Lists ---

    def visit_List(self, node, scope):
        tag = "ol" if node.ordered else "ul"
        start = f' start="{node.start}"' if node.ordered and node.start not in (None, 1) else ""
        self.write(f"<{tag}{start}>")
        self.generic_visit(node, scope)
        self.write(f"</{tag}>")

    def visit_ListItem(self, node, scope):
        self.wrapped("li", node, scope)

    def visit_TaskListItem(self, node, scope):
        self.write("<li>")
        self.text("☑ " if node.checked else "☐ ")
        self.generic_visit(node, scope)
        self.write("</li>")

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
