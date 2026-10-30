"""Puts on one line what every output lays out on one line.

A link's label, a mention's name: the Markdown may spread them over
several lines and pad them with spaces (`[ Acme ](…)`), and no output
keeps that — an anchor shows a break as a space, a post writes one run.
So, right after parsing, a break inside one of them becomes a space and
the whitespace at either end goes: on the tree, once, rather than in every
renderer that lays such a run out. A table cell needs none: the parser
trims it, and it holds no break.
"""

from inkletter.ast import *
from inkletter.visitors.generic import NodeVisitor


class Trimmer(NodeVisitor):
    def visit_UrlLink(self, node, scope):
        self.trim(node, scope)

    def visit_MailLink(self, node, scope):
        self.trim(node, scope)

    def visit_TelLink(self, node, scope):
        self.trim(node, scope)

    def visit_Mention(self, node, scope):
        self.trim(node, scope)

    def trim(self, node, scope):
        """Flatten this node's run, then go on."""
        self.flatten(node)
        self.generic_visit(node, scope)

    @classmethod
    def flatten(cls, node):
        cls.unbreak(node)
        cls.trim_edge(node, leading=True)
        cls.trim_edge(node, leading=False)

    @classmethod
    def trim_edge(cls, node, leading):
        """The whitespace at one end of the run goes, under its marks too
        and past a hand-written tag, up to the first word."""
        children = node.children
        at = 0 if leading else len(children) - 1
        step = 1 if leading else -1
        while 0 <= at < len(children):
            child = children[at]
            if isinstance(child, InlineHtml):
                at += step
                continue
            if cls.blank(child):
                del children[at]
                if not leading:
                    at -= 1
                continue
            if isinstance(child, LiteralText):
                child.value = child.value.lstrip() if leading else child.value.rstrip()
            elif isinstance(child, BlockNode):
                cls.trim_edge(child, leading)
            return

    @classmethod
    def unbreak(cls, node):
        """Every break in the run a space, under its marks too."""
        node.children = [
            LiteralText(" ") if isinstance(child, (SoftBreak, LineBreak)) else child
            for child in node.children
        ]
        for child in node.children:
            if isinstance(child, BlockNode):
                cls.unbreak(child)

    @staticmethod
    def blank(node):
        return isinstance(node, LiteralText) and not node.value.strip()
