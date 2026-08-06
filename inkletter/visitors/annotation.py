from inkletter.ast import *
from inkletter.theme import DEFAULT_THEME, split_media_ratio
from inkletter.visitors.generic import NodeVisitor


class Annotation(NodeVisitor):
    """Decorates the AST with everything the codegen needs to render each
    node — all styling lives here, the codegen only executes.

    There is always a theme.
    """

    def __init__(self, theme):
        self.theme = theme

    def visit_Document(self, node, scope):
        scope.push(node)
        theme = self.theme
        image_attrs = {
            "fluid-on-mobile": "true",
            "align": theme.images.align,
        }
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
        scope.pop(node)

    def mark_text_if_needed(self, node, scope):
        if (
            not scope.get("in_text", False)
            and not scope.get("is_in_table_cell", False)
            and not scope.get("is_in_list_item", False)
            and not scope.get("is_in_button", False)
        ):
            node.annotations["requires_text"] = True
            scope.set("in_text", True)

    def mark_manual_table_if_needed(self, node, scope):
        is_in_list = scope.get("is_in_list", False)
        if is_in_list:
            node.annotations["requires_manual_table"] = True

    def mark_manual_image_if_needed(self, node, scope):
        # Inside the raw HTML of an mj-text (in_text: headings, quotes,
        # lists, inline formatting), of an mj-table or of an mj-button
        # label, an mj-image would leak as an unknown tag: render a
        # plain <img> instead, with its style ready to emit.
        if (
            scope.get("in_text", False)
            or scope.get("is_in_table", False)
            or scope.get("is_in_button", False)
        ):
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
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_TaskListItem(self, node, scope):
        assert isinstance(scope.stack[-1]["node"], List)
        scope.push(node)
        scope.set("is_in_list_item", True)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_ListItem(self, node, scope):
        assert isinstance(scope.stack[-1]["node"], List)
        scope.push(node)
        scope.set("is_in_list_item", True)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Paragraph(self, node, scope):
        scope.push(node)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_BlockText(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
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
        scope.set("is_in_table", True)
        self.mark_manual_table_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_TableHeaderCell(self, node, scope):
        scope.push(node)
        scope.set("is_in_table_cell", True)
        table = self.theme.table
        style = (
            f"border-bottom: 2px solid {table.border_color};"
            f" padding: {table.cell_padding};"
        )
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
        scope.set("is_in_table_cell", True)
        table = self.theme.table
        node.annotations["cell_style"] = (
            f"border-bottom: 1px solid {table.border_color};"
            f" padding: {table.cell_padding};"
        )
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Button(self, node, scope):
        scope.push(node)
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
            node.annotations["media_direction"] = (
                "rtl" if node.side == "right" else None
            )
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Image(self, node, scope):
        scope.push(node)
        self.mark_manual_image_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_ImageLink(self, node, scope):
        scope.push(node)
        self.mark_manual_image_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Heading(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_LiteralText(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Emphasis(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Strong(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_StrikeThrough(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_CodeSpan(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_InlineHtml(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)

    def mark_raw_if_needed(self, node, scope):
        # Outside of any raw-HTML context (mj-text content, table, list item),
        # raw content must be wrapped in mj-raw to be valid MJML.
        node.annotations["requires_raw"] = not (
            scope.get("in_text", False)
            or scope.get("is_in_table_cell", False)
            or scope.get("is_in_list_item", False)
            or scope.get("is_in_button", False)
        )

    def visit_BlockHtml(self, node, scope):
        scope.push(node)
        self.mark_raw_if_needed(node, scope)
        scope.pop(node)

    def visit_TemplateStatement(self, node, scope):
        # flow control wraps whole elements, so it sits in the column
        # between them: same rule as raw HTML
        scope.push(node)
        self.mark_raw_if_needed(node, scope)
        scope.pop(node)

    def visit_TemplateTag(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)

    def visit_ThematicBreak(self, node, scope):
        scope.push(node)
        node.annotations["divider_attrs"] = {
            "border-color": self.theme.divider.color,
            "border-width": self.theme.divider.width,
        }
        scope.pop(node)

    def visit_LineBreak(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)

    def visit_SoftBreak(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)
