from inkletter.ast import *
from inkletter.visitors.generic import NodeVisitor


class Annotation(NodeVisitor):

    def mark_text_if_needed(self, node, scope):
        if (
            not scope.get("in_text", False)
            and not scope.get("is_in_table_cell", False)
            and not scope.get("is_in_list_item", False)
        ):
            node.annotations["requires_text"] = True
            scope.set("in_text", True)

    def mark_manual_table_if_needed(self, node, scope):
        is_in_list = scope.get("is_in_list", False)
        if is_in_list:
            node.annotations["requires_manual_table"] = True

    def mark_manual_image_if_needed(self, node, scope):
        is_in_table = scope.get("is_in_table", False)
        is_in_heading = scope.get("is_in_heading", False)
        is_in_blockquote = scope.get("is_in_blockquote", False)
        is_in_list = scope.get("is_in_list", False)
        if is_in_table or is_in_heading or is_in_blockquote or is_in_list:
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
        scope.set("is_in_blockquote", True)
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

    def visit_ImageRow(self, node, scope):
        scope.push(node)
        # Tell the codegen this node renders as its own multi-column
        # section, and each image that it sits in a row (row spacing).
        node.annotations["own_section"] = True
        for image in node.children:
            image.annotations["in_image_row"] = True
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_MediaObject(self, node, scope):
        scope.push(node)
        node.annotations["own_section"] = True
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
        scope.set("is_in_heading", True)
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
        )
        scope.pop(node)

    def visit_ThematicBreak(self, node, scope):
        scope.push(node)
        scope.pop(node)

    def visit_LineBreak(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)

    def visit_SoftBreak(self, node, scope):
        scope.push(node)
        self.mark_text_if_needed(node, scope)
        scope.pop(node)
