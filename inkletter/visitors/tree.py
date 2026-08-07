from inkletter.visitors.generic import NodeVisitor


class TreeVisitor(NodeVisitor):
    def __init__(self):
        super().__init__()
        self.lines = []
        self._indent = 0

    def render(self, node):
        self.visit(node, scope=None)
        return "\n".join(self.lines)

    def write(self, text):
        self.lines.append("  " * self._indent + text)

    def generic_visit(self, node, scope=None):
        self.write(repr(node))
        self._indent += 1
        for child in node.get_children():
            self.generic_visit(child, scope)
        self._indent -= 1


def print_tree(doc):
    visitor = TreeVisitor()
    output = visitor.render(doc)
    print("\n" + output)
