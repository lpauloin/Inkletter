from inkletter.ast import *
from inkletter.visitors.generic import NodeVisitor


class BlockTextMerger(NodeVisitor):
    def __init__(self, bold_link_is_button=True):
        self.bold_link_is_button = bold_link_is_button

    def merge_inline_sequences(self, children):
        new_children = []
        buffer = []

        def clean(_buf):
            while _buf:
                if isinstance(_buf[0], TextTerminal):
                    _buf.pop(0)
                    continue
                if isinstance(_buf[-1], TextTerminal):
                    _buf.pop(-1)
                    continue
                break

        def flush(_buf, _children):
            clean(_buf)
            if _buf:
                _children.append(BlockText(_buf.copy()))
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
        scope.push(node)
        # The alt may contain formatting nodes; merge them into a single
        # LiteralText since the HTML alt attribute cannot hold markup.
        # The collector rides the scope, so nesting takes care of itself.
        if isinstance(node.alt_text, list):
            scope.set("alt_parts", [])
            self.generic_visit(node, scope)
            node.alt_text = LiteralText("".join(scope.get("alt_parts")))
        scope.pop(node)

    def visit_ImageLink(self, node, scope):
        scope.push(node)
        self.generic_visit(node, scope)
        scope.pop(node)

    def collect_alt(self, scope, text):
        parts = scope.get("alt_parts")
        if parts is not None:
            parts.append(text)

    def visit_LiteralText(self, node, scope):
        self.collect_alt(scope, node.value)

    def visit_CodeSpan(self, node, scope):
        self.collect_alt(scope, node.code)

    def visit_TemplateTag(self, node, scope):
        # without this the tag would simply vanish from an alt
        self.collect_alt(scope, node.raw)

    def visit_Document(self, node, scope):
        scope.push(node)
        node.children = self.merge_inline_sequences(node.children)
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

    def promote_button(self, node, types):
        """A paragraph made only of a bold link becomes a Button (CTA)."""
        blocks = [c for c in node.children if not self.is_blank(c)]
        if len(blocks) != 1 or not isinstance(blocks[0], BlockText):
            return None
        inlines = [c for c in blocks[0].children if not self.is_blank_inline(c)]
        if len(inlines) != 1 or not isinstance(inlines[0], Strong):
            return None
        label = [c for c in inlines[0].children if not self.is_blank_inline(c)]
        if len(label) != 1 or not isinstance(label[0], Link):
            return None
        link = label[0]
        # never a button on an image link: the image always wins, even
        # nested deep inside the label
        if types & {Image, ImageLink}:
            return None
        # the href may already have been rewritten by the URLRewriter
        # pass, which runs before this merger (see parse_markdown_to_ast)
        return Button(link.children, link.href, link.title)

    def is_blank_inline(self, node):
        if isinstance(node, TextTerminal):
            return True
        return isinstance(node, LiteralText) and not node.value.strip()

    def is_blank(self, node):
        if not isinstance(node, BlockText):
            return False
        return all(self.is_blank_inline(c) for c in node.children)

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
