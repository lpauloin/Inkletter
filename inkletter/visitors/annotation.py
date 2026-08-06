from inkletter.ast import *
from inkletter.theme import split_media_ratio
from inkletter.visitors.generic import NodeVisitor


class Annotation(NodeVisitor):
    """Decorates the AST with everything the codegen needs to render each
    node: the codegen visits and executes, all decisions are made here."""

    def __init__(self, theme=None):
        self.theme = theme

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
        # plain <img> instead.
        if (
            scope.get("in_text", False)
            or scope.get("is_in_table", False)
            or scope.get("is_in_button", False)
        ):
            node.annotations["requires_manual_image"] = True

    def visit_List(self, node, scope):
        scope.push(node)
        scope.set("is_in_list", True)
        self.mark_text_if_needed(node, scope)
        self.generic_visit(node, scope)
        node.annotations["is_task_list"] = scope.get("has_task_item", False)
        scope.pop(node)

    def visit_TaskListItem(self, node, scope):
        assert isinstance(scope.stack[-1]["node"], List)
        scope.set("has_task_item", True)
        scope.push(node)
        scope.set("is_in_list_item", True)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_ListItem(self, node, scope):
        assert isinstance(scope.stack[-1]["node"], List)
        scope.set("has_task_item", False)
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
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_TableCell(self, node, scope):
        scope.push(node)
        scope.set("is_in_table_cell", True)
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
        # This node renders as its own multi-column section, and each of
        # its images carries the row spacing to apply.
        node.annotations["own_section"] = True
        gap = self.theme.images.row_gap if self.theme is not None else "8px"
        for image in node.children:
            image.annotations["image_padding"] = f"10px {gap}"
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_MediaObject(self, node, scope):
        scope.push(node)
        node.annotations["own_section"] = True
        # Full render instructions: layout mode, column widths, and the
        # desktop-only rtl flip for side=right (image stays first in the
        # DOM so it stacks on top on mobile).
        if self.theme is not None and self.theme.images.text_layout == "stacked":
            node.annotations["media_layout"] = "stacked"
        else:
            node.annotations["media_layout"] = "columns"
            ratio = self.theme.images.media_ratio if self.theme else "30%"
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

    def visit_Text(self, node, scope):
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

    def visit_BlockHtml(self, node, scope):
        scope.push(node)
        # Outside of any raw-HTML context (mj-text content, table, list item),
        # raw HTML must be wrapped in mj-raw to be valid MJML.
        node.annotations["requires_raw"] = not (
            scope.get("in_text", False)
            or scope.get("is_in_table_cell", False)
            or scope.get("is_in_list_item", False)
            or scope.get("is_in_button", False)
        )
        scope.pop(node)

    def visit_ThematicBreak(self, node, scope):
        scope.push(node)
        # Themed dividers are styled by the head mj-attributes; without a
        # theme the legacy hardcoded style applies.
        if self.theme is None:
            node.annotations["divider_attrs"] = {
                "border-color": "#cccccc",
                "border-width": "1px",
            }
        else:
            node.annotations["divider_attrs"] = {}
        scope.pop(node)

    def visit_LineBreak(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)

    def visit_SoftBreak(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)
