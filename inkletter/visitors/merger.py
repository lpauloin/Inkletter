from inkletter.ast import *
from inkletter.visitors.generic import NodeVisitor


class BlockTextMerger(NodeVisitor):
    """Groups each run of inline nodes of a paragraph or a heading into a
    BlockText, and promotes the paragraphs a layout convention names: an
    image row, an image beside its text, a button."""

    def __init__(self, bold_link_is_button=True):
        super().__init__()
        self.bold_link_is_button = bold_link_is_button

    @classmethod
    def merge_inline_sequences(cls, children):
        merged, buffer = [], []
        for child in children:
            if isinstance(child, Text):
                buffer.append(child)
                continue
            cls.flush(buffer, merged)
            merged.append(child)
        cls.flush(buffer, merged)
        return merged

    @staticmethod
    def flush(buffer, merged):
        """The run gathered so far as a BlockText, the breaks at its edges
        aside — an image between two lines leaves one on either side."""
        while buffer and isinstance(buffer[0], TextTerminal):
            buffer.pop(0)
        while buffer and isinstance(buffer[-1], TextTerminal):
            buffer.pop()
        if buffer:
            merged.append(BlockText(buffer.copy()))
            buffer.clear()

    def process_blocknode(self, node, scope):
        node.children = self.merge_inline_sequences(node.children)
        for child in node.children:
            self.visit(child, scope)

    def visit_Paragraph(self, node, scope):
        self.process_blocknode(node, scope)

    def visit_Heading(self, node, scope):
        self.process_blocknode(node, scope)

    # An image announces itself to the paragraph asking what it holds
    # (`promote_button`): pushed on the scope, the one place types are
    # recorded.

    def visit_Image(self, node, scope):
        scope.push(node)
        scope.pop(node)

    def visit_ImageLink(self, node, scope):
        scope.push(node)
        self.generic_visit(node, scope)
        scope.pop(node)

    def visit_Document(self, node, scope):
        scope.push(node)
        promoted = []
        for child in node.children:
            # record afresh: each child is promoted on what it holds
            scope.record_types()
            self.visit(child, scope)
            promoted.extend(self.promote_paragraph(child, scope.types()))
        node.children = promoted
        scope.pop(node)

    def promote_paragraph(self, node, types):
        """Turn image-only paragraphs into ImageRow(s) and image-beside-text
        paragraphs into MediaObject (top-level layout conventions)."""
        if not isinstance(node, Paragraph):
            return [node]
        images = [c for c in node.children if isinstance(c, (Image, ImageLink))]
        others = [c for c in node.children if not isinstance(c, (Image, ImageLink))]
        if not images:
            if self.bold_link_is_button:
                button = self.promote_button(node, types)
                if button is not None:
                    return [button]
            return [node]

        if all(self.is_blank(c) for c in others):
            if len(images) == 1:
                # drop the blank filler around a lone image
                node.children = images
                return [node]
            # up to 4 images stay on one row, more wrap into rows of 3
            if len(images) <= 4:
                return [ImageRow(images)]
            return [ImageRow(images[i : i + 3]) for i in range(0, len(images), 3)]

        if len(images) == 1:
            if node.children[0] is images[0]:
                self.strip_edge(others, leading=True)
                return [MediaObject(images[0], others, side="left")]
            if node.children[-1] is images[0]:
                self.strip_edge(others, leading=False)
                return [MediaObject(images[0], others, side="right")]
        return [node]

    @classmethod
    def promote_button(cls, node, types):
        """A paragraph made only of a bold link becomes a Button (CTA)."""
        blocks = [c for c in node.children if not cls.is_blank(c)]
        if len(blocks) != 1 or not isinstance(blocks[0], BlockText):
            return None
        inlines = [c for c in blocks[0].children if not c.is_blank()]
        if len(inlines) != 1 or not isinstance(inlines[0], Strong):
            return None
        link = inlines[0].ask
        if link is None:
            return None
        # never a button on an image link: the image always wins, even
        # nested deep inside the label
        if types & {Image, ImageLink}:
            return None
        return Button(link.children, link.href, link.title)

    @staticmethod
    def is_blank(node):
        if not isinstance(node, BlockText):
            return False
        return all(c.is_blank() for c in node.children)

    @staticmethod
    def strip_edge(blocks, leading):
        """Trim the whitespace left over next to the extracted image."""
        if not blocks:
            return
        block = blocks[0] if leading else blocks[-1]
        if not isinstance(block, BlockText) or not block.children:
            return
        text = block.children[0] if leading else block.children[-1]
        if isinstance(text, LiteralText):
            text.value = text.value.lstrip() if leading else text.value.rstrip()
