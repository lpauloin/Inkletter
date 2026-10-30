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
        children = [
            LiteralText(" ") if isinstance(child, (SoftBreak, LineBreak)) else child
            for child in node.children
        ]
        while children and cls.blank(children[0]):
            children.pop(0)
        while children and cls.blank(children[-1]):
            children.pop()
        if children and isinstance(children[0], LiteralText):
            children[0].value = children[0].value.lstrip()
        if children and isinstance(children[-1], LiteralText):
            children[-1].value = children[-1].value.rstrip()
        node.children = children

    @staticmethod
    def blank(node):
        return isinstance(node, LiteralText) and not node.value.strip()
