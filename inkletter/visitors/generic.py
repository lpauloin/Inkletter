from inkletter.visitors.scope import ScopeStack


class NodeVisitor:
    def __init__(self):
        self.scope = ScopeStack()

    def visit(self, node, scope=None):
        """Dispatch to the appropriate visit method or fallback to generic_visit."""
        scope = self.scope if scope is None else scope
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, scope)

    def generic_visit(self, node, scope):
        """Default visit method if no visit_XXX found."""
        for child in node.get_children():
            self.visit(child, scope)
