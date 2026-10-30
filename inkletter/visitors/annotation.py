import re

from inkletter.ast import *
from inkletter.plugins.bare_domains import is_bare_domain
from inkletter.theme import split_media_ratio
from inkletter.visitors.generic import NodeVisitor

#: The href of a hand-written opening anchor: what the outputs that cannot
#: pass the tag through — text, post, fragment — spell or rebuild.
ANCHOR_HREF = re.compile(r'<a\s[^>]*\bhref\s*=\s*["\']([^"\']*)["\']', re.I)


def is_an_address(label):
    """Whether a label is an address already — with its scheme, or a domain
    written without one — rather than a name for one."""
    return Link.scheme_of(label) in ("http", "https") or is_bare_domain(label)


class Annotation(NodeVisitor):
    """Decorates the AST with everything the codegen needs to render each
    node — all styling lives here, the codegen only executes.

    There is always a theme.
    """

    def __init__(self, theme, link_attributes=True):
        super().__init__()
        self.theme = theme
        self.link_attributes = link_attributes

    def visit_Document(self, node, scope):
        scope.push(node)
        # an empty slot the first h1 fills in, with its text or with
        # None when it turns out not to be usable as a title
        scope.set("document_title", [])
        # what the document writes that a feed will not show: the styles on
        # its words, look-alikes or not, and its headings
        scope.set("document", node)
        scope.set("styles_written", set())
        node.annotations["has_headings"] = False
        theme = self.theme
        image_attrs = {"align": theme.images.align}
        if not self.link_attributes:
            # without link attributes no image carries a width of its
            # own: each takes the full width of a phone's screen
            image_attrs["fluid-on-mobile"] = "true"
        if theme.images.border_radius not in ("0", "0px"):
            image_attrs["border-radius"] = theme.images.border_radius
        node.annotations["head"] = {
            # mj-table and mj-button have their own MJML defaults
            # (black Ubuntu 13px) and must follow the theme instead
            "attributes": {
                "mj-section": {
                    "padding": theme.layout.section_padding,
                    "background-color": theme.layout.content_background_color,
                },
                "mj-text": {
                    "font-family": theme.text.font_family,
                    "font-size": theme.text.font_size,
                    "line-height": theme.text.line_height,
                    "color": theme.text.color,
                },
                "mj-table": {
                    "color": theme.text.color,
                    "font-family": theme.text.font_family,
                    "font-size": theme.text.font_size,
                    "line-height": theme.text.line_height,
                },
                "mj-button": {
                    "background-color": theme.button_background(),
                    "color": theme.buttons.color,
                    "border-radius": theme.buttons.border_radius,
                    "font-weight": theme.buttons.font_weight,
                    "inner-padding": theme.buttons.padding,
                    "align": theme.buttons.align,
                    "font-family": theme.text.font_family,
                    "font-size": theme.text.font_size,
                },
                "mj-image": image_attrs,
            },
            "css": theme.to_css(),
            "fonts": theme.fonts,
        }
        node.annotations["body_attrs"] = {
            "width": theme.layout.width,
            "background-color": theme.layout.background_color,
        }
        self.generic_visit(node, scope)
        node.annotations["styles_written"] = frozenset(scope.get("styles_written"))
        found = scope.get("document_title")
        node.annotations["head"]["title"] = found[0] if found else None
        scope.pop(node)

    def add_style(self, scope, style):
        """Bold, italic, strikethrough: the styles in force below, carried
        down to every text they cover."""
        scope.set("styles", scope.get("styles", frozenset()) | {style})

    def mark_styles(self, node, scope, text):
        # a mention's name is never dressed: it is what the platform matches
        styles = scope.get("styles")
        if styles and not scope.get("is_in_mention") and not scope.get("is_in_address"):
            node.annotations["styles"] = styles
            # spaces alone wear no style a reader could miss
            if text.strip():
                scope.get("styles_written").update(styles)

    @staticmethod
    def in_raw_html(scope):
        """Whether a node sits in raw HTML already — an mj-text's content, a
        table, a list item, a button's label — where no MJML component may
        open."""
        return (
            scope.get("in_text", False)
            or scope.get("is_in_table", False)
            or scope.get("is_in_list_item", False)
            or scope.get("is_in_button", False)
        )

    def mark_text_if_needed(self, node, scope):
        if not self.in_raw_html(scope):
            node.annotations["requires_text"] = True
            scope.set("in_text", True)

    def mark_manual_table_if_needed(self, node, scope):
        # in raw HTML — a list, a quote, a cell — an mj-table is an unknown tag
        if self.in_raw_html(scope):
            node.annotations["requires_manual_table"] = True

    def apply_author_attributes(self, node):
        """Fold what the author asked for into the render instructions.

        The theme keeps deciding how images look; the document only
        says how wide this one is, and where it sits. A manual <img>
        has no attributes of its own, so its facts go into the style it
        already carries — and an alignment means nothing there, an
        image in a run of text sits where the text puts it.
        """
        attributes = node.attributes
        if not attributes:
            return
        if node.annotations.get("requires_manual_image"):
            sizes = [
                f"{name}: {value};"
                for name, value in (("width", attributes.width), ("height", attributes.height))
                if value
            ]
            if sizes:
                node.annotations["image_style"] += " " + " ".join(sizes)
            return
        node.annotations["image_size"] = {
            name: value
            for name, value in (
                ("width", attributes.width),
                ("height", attributes.height),
                ("align", attributes.align),
            )
            if value
        }

    def mark_manual_image_if_needed(self, node, scope):
        # In raw HTML an mj-image would leak as an unknown tag: render a
        # plain <img> instead, with its style ready to emit.
        if self.in_raw_html(scope):
            node.annotations["requires_manual_image"] = True
            style = "max-width: 100%; height: auto;"
            radius = self.theme.images.border_radius
            if radius not in ("0", "0px"):
                style += f" border-radius: {radius};"
            node.annotations["image_style"] = style

    def visit_List(self, node, scope):
        scope.push(node)
        scope.set("is_in_list", True)
        self.mark_text_if_needed(node, scope)
        # an ordered list numbers its items from its start, a box included,
        # as a reader of the mail counts them — a rank is a matter between
        # siblings
        if node.ordered:
            start = 1 if node.start is None else node.start
            for offset, item in enumerate(node.elements):
                item.annotations["number"] = start + offset
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_TaskListItem(self, node, scope):
        assert isinstance(scope.stack[-1]["node"], List)
        scope.push(node)
        self.open_anchor_run(scope)
        # the box opens the item's first line, drawn by whoever writes it
        if node.children:
            node.children[0].annotations["checkbox"] = "☑" if node.checked else "☐"
        scope.set("is_in_list_item", True)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_ListItem(self, node, scope):
        assert isinstance(scope.stack[-1]["node"], List)
        scope.push(node)
        self.open_anchor_run(scope)
        scope.set("is_in_list_item", True)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Paragraph(self, node, scope):
        scope.push(node)
        self.open_anchor_run(scope)
        # At flow level each paragraph gets its own mj-text, and the
        # padding between them is what separates them. Inside a
        # raw-HTML context — a quote, a list item, a cell — there is no
        # such padding, so the paragraph must carry its own tag or it
        # runs into its neighbour.
        node.annotations["requires_paragraph_tag"] = self.in_raw_html(scope)
        if not node.annotations["requires_paragraph_tag"]:
            # At flow level an image is a block of its own, stacked between
            # the lines around it: the breaks beside it separate what the
            # mail already sets apart.
            for child in node.children:
                if isinstance(child, TextTerminal):
                    child.annotations["between_blocks"] = True
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_BlockText(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.mark_the_asks(node)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_BlockQuote(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_BlockCode(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Table(self, node, scope):
        scope.push(node)
        self.mark_manual_table_if_needed(node, scope)
        scope.set("is_in_table", True)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_TableHeaderCell(self, node, scope):
        scope.push(node)
        self.open_anchor_run(scope)
        table = self.theme.table
        style = f"border-bottom: 2px solid {table.border_color}; padding: {table.cell_padding};"
        if table.header_color:
            style += f" color: {table.header_color};"
        if table.header_background_color:
            style += f" background-color: {table.header_background_color};"
        if not node.align:
            style += " text-align: left;"
        node.annotations["cell_style"] = style
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_TableCell(self, node, scope):
        scope.push(node)
        self.open_anchor_run(scope)
        table = self.theme.table
        node.annotations["cell_style"] = (
            f"border-bottom: 1px solid {table.border_color}; padding: {table.cell_padding};"
        )
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Button(self, node, scope):
        scope.push(node)
        self.open_anchor_run(scope)
        # The one link of the document that is the ask, said in the node
        # for whoever handles URLs after this pass.
        node.annotations["button"] = True
        # The label is a raw-HTML-inline context: no mj-text inside,
        # no MJML component of any kind.
        scope.set("is_in_button", True)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_ImageRow(self, node, scope):
        scope.push(node)
        # A row defines its own column layout: it cannot live inside the
        # single-column flow section, it emits its own mj-section. Each
        # image carries the row spacing to apply.
        node.annotations["defines_own_columns"] = True
        gap = self.theme.images.row_gap
        for image in node.children:
            image.annotations["image_padding"] = f"10px {gap}"
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_MediaObject(self, node, scope):
        scope.push(node)
        self.open_anchor_run(scope)
        # Same as ImageRow: its 30/70 columns need their own mj-section.
        node.annotations["defines_own_columns"] = True
        # Full render instructions: layout mode, column widths, and the
        # desktop-only rtl flip for side=right (image stays first in the
        # DOM so it stacks on top on mobile).
        if self.theme.images.text_layout == "stacked":
            node.annotations["media_layout"] = "stacked"
        else:
            node.annotations["media_layout"] = "columns"
            ratio = self.theme.images.media_ratio
            node.annotations["media_widths"] = split_media_ratio(ratio)
            node.annotations["media_direction"] = "rtl" if node.side == "right" else None
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Image(self, node, scope):
        scope.push(node)
        self.mark_manual_image_if_needed(node, scope)
        self.apply_author_attributes(node)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_ImageLink(self, node, scope):
        scope.push(node)
        node.annotations["bold"] = scope.get("is_in_strong", False)
        self.generic_visit(node, scope)  # reaches node.img -> visit_Image
        scope.pop(node)

    def visit_Heading(self, node, scope):
        scope.push(node)
        self.open_anchor_run(scope)
        scope.get("document").annotations["has_headings"] = True
        # Only the first h1 of the document body is its title, and only
        # if it holds nothing but text — anything else disqualifies it
        # rather than being flattened away. in_text already tells us the
        # heading sits in a quote, a list or a cell.
        slot = scope.get("document_title")
        claims_title = node.level == 1 and not scope.get("in_text") and not slot
        if claims_title:
            scope.record_types()
            scope.set("title_parts", [])
        self.mark_text_if_needed(node, scope)
        # Alignment rides the mj-text attribute rather than the head
        # CSS: it comes out both as `td align` and as an inlined
        # text-align, where a `h1 { text-align }` rule would depend on a
        # <style> block some clients drop. Left is MJML's own default,
        # so nothing is emitted for it.
        align = self.theme.headings.at(node.level).align
        if node.annotations.get("requires_text") and align != "left":
            node.annotations["text_attrs"] = {"align": align}
        self.generic_visit(node, scope)
        if claims_title:
            # listing what a title may hold rather than what it may not:
            # a node type added later disqualifies it on its own
            plain = scope.types() <= {BlockText, LiteralText}
            text = "".join(scope.get("title_parts")).strip()
            slot.append(text if plain and text else None)
        scope.pop(node)

    def visit_LiteralText(self, node, scope):
        scope.push(node)
        parts = scope.get("title_parts")
        if parts is not None:
            parts.append(node.value)
        self.mark_styles(node, scope, node.value)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Emphasis(self, node, scope):
        scope.push(node)
        self.add_style(scope, "italic")
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Strong(self, node, scope):
        scope.push(node)
        scope.set("is_in_strong", True)
        # The ask still says it was bold, for the URL factory, but its words
        # keep their own letters: on a feed a call to action is a line of
        # text. A bold link among words is emphasis, styled as such.
        if not node.annotations.get("ask"):
            self.add_style(scope, "bold")
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_StrikeThrough(self, node, scope):
        scope.push(node)
        self.add_style(scope, "strikethrough")
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_UrlLink(self, node, scope):
        label = node.plain_text()
        self.link(node, scope, not label or label == node.href or is_an_address(label))

    def visit_MailLink(self, node, scope):
        label = node.plain_text()
        self.link(node, scope, not label or label in (node.address, node.href))

    def visit_TelLink(self, node, scope):
        label = node.plain_text()
        self.link(node, scope, not label or label in (node.number, node.href))

    def link(self, node, scope, label_is_address):
        scope.push(node)
        # Said in the node for whoever handles URLs after this pass: a
        # link inside bold text is the ask where no button exists.
        node.annotations["bold"] = scope.get("is_in_strong", False)
        # A label that is an address already — the target itself, the one
        # the parser wrapped around a bare address, or another — is not a
        # name for it: where the target is shown, it is not shown twice,
        # and its words are no styled text.
        node.annotations["label_is_address"] = label_is_address
        if label_is_address:
            scope.set("is_in_address", True)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Mention(self, node, scope):
        scope.push(node)
        scope.set("is_in_mention", True)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Hashtag(self, node, scope):
        scope.push(node)
        # The mail may set it apart, when its theme says so; the feed never
        # touches it — in look-alikes a tag would be another tag.
        color = self.theme.hashtags.color
        if color:
            node.annotations["hashtag_style"] = f"color: {color};"
        self.mark_text_if_needed(node, scope)
        scope.pop(node)

    def visit_CodeSpan(self, node, scope):
        scope.push(node)
        self.mark_styles(node, scope, node.code)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_InlineHtml(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.mark_anchor(node, scope)
        scope.pop(node)

    @staticmethod
    def open_anchor_run(scope):
        """A block where hand-written anchors pair up: an opening tag and
        its closing one sit in the same paragraph, heading, cell or item,
        whatever marks or images stand between them."""
        scope.set("anchors", [])

    @staticmethod
    def mark_anchor(node, scope):
        """Say which hand-written tags open and close an anchor, and hand
        the closing one the URL its opening tag carried.

        The text output has no tags to show, so a hand-written <a>
        would lose its URL where a Markdown link keeps it — silently,
        in the half meant to stay readable everywhere; the fragment
        rebuilds the anchor from its URL alone. Pairing an opening tag
        with its closing one is a matter of document order, so it belongs
        here rather than in a codegen.
        """
        pending = scope.get("anchors")
        if pending is None:
            return
        value = node.value.strip()
        opening = ANCHOR_HREF.match(value)
        if opening:
            # what runs something is no link, hand-written or not: its
            # closing tag is still its own, never an outer anchor's
            href = None if runs_something(opening.group(1)) else opening.group(1)
            # an anchor inside another is no tag a page can hold: its
            # address is still said where words carry it
            nested = any(outer is not None for outer, _ in pending)
            if href is not None:
                node.annotations["anchor_opens"] = href
                node.annotations["anchor_nested"] = nested
            pending.append((href, nested))
        elif value.lower() == "</a>" and pending:
            href, nested = pending.pop()
            if href is not None:
                node.annotations["anchor_href"] = href
                node.annotations["anchor_nested"] = nested

    @staticmethod
    def mark_the_asks(node):
        """Say which bold link is the ask — where no button exists: alone on
        its line, blanks aside. Which line a node is on is a matter between
        siblings, so it belongs here rather than in a codegen."""
        line = []
        for child in [*node.children, LineBreak()]:
            if not isinstance(child, (SoftBreak, LineBreak)):
                line.append(child)
                continue
            alone = Annotation.alone(line)
            # through the marks that wrap it alone: `*__[Réserver](…)__*`
            while isinstance(alone, (Emphasis, StrikeThrough)):
                alone = Annotation.alone(alone.children)
            if isinstance(alone, Strong) and alone.ask is not None:
                alone.annotations["ask"] = True
            line = []

    @staticmethod
    def alone(nodes):
        """The one node of a run, blanks aside, or None."""
        inner = [node for node in nodes if not node.is_blank()]
        return inner[0] if len(inner) == 1 else None

    def mark_raw_if_needed(self, node, scope):
        # Outside raw HTML, raw content must be wrapped in mj-raw to be
        # valid MJML.
        node.annotations["requires_raw"] = not self.in_raw_html(scope)

    def visit_BlockHtml(self, node, scope):
        scope.push(node)
        self.mark_raw_if_needed(node, scope)
        scope.pop(node)

    def visit_ThematicBreak(self, node, scope):
        scope.push(node)
        node.annotations["divider_attrs"] = {
            "border-color": self.theme.divider.color,
            "border-width": self.theme.divider.width,
        }
        scope.pop(node)

    def visit_LineBreak(self, node, scope):
        self.break_(node, scope)

    def visit_SoftBreak(self, node, scope):
        self.break_(node, scope)

    def break_(self, node, scope):
        scope.push(node)
        if not node.annotations.get("between_blocks"):
            self.mark_text_if_needed(node, scope)
        scope.pop(node)
