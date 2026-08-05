from inkletter.ast import *
from inkletter.visitors.generic import NodeVisitor


class BlockTextMerger(NodeVisitor):
    def __init__(self):
        self._text_parts = None

    def merge_inline_sequences(self, children):
        new_children = []
        buffer = []

        def clean(_buf):
            while _buf:
                if isinstance(_buf[0], TextTerminal):
                    _buf.pop(0)
                    continue
                if isinstance(_buf[-1], TextTerminal):
                    buffer.pop(-1)
                    continue
                break

        def flush(_buf, _children):
            clean(_buf)
            if _buf:
                _children.append(BlockText(buffer.copy()))
                _buf.clear()

        for child in children:
            if isinstance(child, Text):
                buffer.append(child)
            elif isinstance(child, BlockText):
                flush(buffer, new_children)
                new_children.append(child)
            else:
                flush(buffer, new_children)
                new_children.append(child)

        flush(buffer, new_children)
        return new_children

    def process_blocknode(self, node, scope):
        assert hasattr(node, "children")
        node.children = self.merge_inline_sequences(node.children)
        for child in node.children:
            self.visit(child, scope)

    def visit_Image(self, node, scope):
        # The alt may contain formatting nodes; merge them into a single
        # LiteralText since the HTML alt attribute cannot hold markup.
        if isinstance(node.alt_text, list):
            parts, self._text_parts = self._text_parts, []
            self.generic_visit(node, scope)
            node.alt_text = LiteralText("".join(self._text_parts))
            self._text_parts = parts

    def visit_LiteralText(self, node, scope):
        if self._text_parts is not None:
            self._text_parts.append(node.value)

    def visit_CodeSpan(self, node, scope):
        if self._text_parts is not None:
            self._text_parts.append(node.code)

    def visit_Document(self, node, scope):
        self.process_blocknode(node, scope)
        node.children = [self.promote_paragraph(c) for c in node.children]

    def promote_paragraph(self, node):
        """Turn image-only paragraphs into ImageRow and image-beside-text
        paragraphs into MediaObject (top-level layout conventions)."""
        if not isinstance(node, Paragraph):
            return node
        images = [c for c in node.children if isinstance(c, (Image, ImageLink))]
        others = [c for c in node.children if not isinstance(c, (Image, ImageLink))]
        if not images:
            return node

        if all(self.is_blank(c) for c in others):
            if len(images) == 1:
                # drop the blank filler around a lone image
                node.children = images
                return node
            return ImageRow(images)

        if len(images) == 1:
            if node.children[0] is images[0]:
                self.strip_edge(others, leading=True)
                return MediaObject(images[0], others, side="left")
            if node.children[-1] is images[0]:
                self.strip_edge(others, leading=False)
                return MediaObject(images[0], others, side="right")
        return node

    def is_blank(self, node):
        if not isinstance(node, BlockText):
            return False
        return all(
            isinstance(c, TextTerminal)
            or (isinstance(c, LiteralText) and not c.value.strip())
            for c in node.children
        )

    def strip_edge(self, blocks, leading):
        """Trim the whitespace left over next to the extracted image."""
        if not blocks:
            return
        block = blocks[0] if leading else blocks[-1]
        if not isinstance(block, BlockText) or not block.children:
            return
        text = block.children[0] if leading else block.children[-1]
        if isinstance(text, LiteralText):
            text.value = text.value.lstrip() if leading else text.value.rstrip()

    def visit_Paragraph(self, node, scope):
        self.process_blocknode(node, scope)

    def visit_ListItem(self, node, scope):
        self.process_blocknode(node, scope)

    def visit_TaskListItem(self, node, scope):
        self.process_blocknode(node, scope)

    def visit_BlockQuote(self, node, scope):
        self.process_blocknode(node, scope)

    def visit_Heading(self, node, scope):
        self.process_blocknode(node, scope)
