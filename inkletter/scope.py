TYPES = "node_types"


class ScopeStack:
    """The context a visitor carries as it walks down the tree.

    A value set on a scope is visible to everything below it and dies
    with it, which covers the inherited flags (in_text, is_in_button…).
    Two ways round the one-way street, when a scope needs to know about
    its own subtree: record_types, for what node types live below, and
    an ordinary mutable value that descendants fill in.
    """

    def __init__(self):
        self.stack = []

    def push(self, node):
        self.stack.append({"node": node})
        # every node announces its type to whoever is recording below
        for frame in reversed(self.stack):
            if TYPES in frame:
                frame[TYPES].add(type(node))
                return

    def pop(self, node):
        if not self.stack:
            raise RuntimeError("Scope underflow")
        top = self.stack.pop()
        if top["node"] != node:
            raise RuntimeError("Scope mismatch: expected %s, got %s" % (top["node"], node))
        return top

    def set(self, key, value):
        if not self.stack:
            raise RuntimeError("No active scope")
        self.stack[-1][key] = value

    def get(self, key, default=None):
        for frame in reversed(self.stack):
            if key in frame:
                return frame[key]
        return default

    def record_types(self):
        """Record the node classes living under this scope.

        Lets a scope ask "what am I made of?" without walking its own
        subtree — and as a whitelist: a node type nobody thought about
        shows up in the set instead of slipping through unnoticed.
        """
        self.set(TYPES, set())

    def types(self):
        return self.get(TYPES, set())

    def __repr__(self):
        lines = ["ScopeStack:"]
        for i, frame in enumerate(self.stack):
            node = frame.get("node")
            node_name = repr(node)
            other_keys = {k: v for k, v in frame.items() if k != "node"}
            if other_keys:
                lines.append(f"  [{i}] {node_name} {other_keys}")
            else:
                lines.append(f"  [{i}] {node_name}")
        return "\n".join(lines)
