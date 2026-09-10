INDENT_SIZE = 2  # Number of spaces per indent level
NEWLINE = "\n"  # Newline character


# Base class for all elements
class CodeElement:
    def accept(self, visitor):
        raise NotImplementedError()


# Concrete element classes
class Indent(CodeElement):
    """One more prefix on every line that follows, until the matching
    Dedent: the indentation spaces by default, but a quote's `> ` just as
    well — a prefix is a prefix."""

    def __init__(self, prefix=None):
        self.prefix = prefix

    def accept(self, visitor):
        return visitor.visit_indent(self)


class Dedent(CodeElement):
    def accept(self, visitor):
        return visitor.visit_dedent(self)


class Newline(CodeElement):
    def accept(self, visitor):
        return visitor.visit_newline(self)


class TextElement(CodeElement):
    """A run of text, and what it costs where cost is counted.

    `cost` is None for text that costs its own characters — nearly all of
    it. It is set where the two differ, so that a resolver sums prices
    declared at the moment of writing rather than re-reading the finished
    string.
    """

    def __init__(self, text, indented=True, cost=None):
        self.text = text
        self.indented = indented
        self.cost = cost

    def accept(self, visitor):
        return visitor.visit_text(self)


# The main CodeBlock class
class CodeBlock(CodeElement):
    def __init__(self):
        self.elements = []

    def add_indent(self, prefix=None):
        self.elements.append(Indent(prefix))

    def add_dedent(self):
        self.elements.append(Dedent())

    def add_text(self, text, indented=True, cost=None):
        self.elements.append(TextElement(text, indented=indented, cost=cost))

    def add_newline(self):
        self.elements.append(Newline())

    def add_codeblock(self, cb):
        self.elements.append(cb)

    def accept(self, visitor):
        return visitor.visit_codeblock(self)


# Visitor to resolve the CodeBlock to a string
class CodeBlockResolver:
    """Resolves a block to text, and weighs it on the way.

    Every line costs its prefixes, its fragments — what they declared, or
    `measure` of what they say — and the break that ends it. `measure` is
    the caller's unit, `len` unless told otherwise: nothing here knows
    what any platform counts. Trailing whitespace goes from every line,
    from plain text only — what is priced never ends with any.
    """

    def __init__(self, indent_size=INDENT_SIZE, starting_indent=0, measure=len):
        self.indent = " " * indent_size
        self.starting_indent = starting_indent
        self.measure = measure
        self.reset()

    def reset(self):
        self.prefixes = [self.indent] * self.starting_indent
        self.lines = []  # (text, cost), one per line
        self.parts = None  # the line being built, [(text, cost)], or None

    def visit_indent(self, node):
        self.prefixes.append(self.indent if node.prefix is None else node.prefix)

    def visit_dedent(self, node):
        if len(self.prefixes) <= self.starting_indent:
            raise ValueError("Cannot dedent below zero")
        self.prefixes.pop()

    def visit_newline(self, node):
        if self.parts is None:
            self.parts = [("".join(self.prefixes), None)]
        self.close_line()

    def visit_text(self, node):
        if self.parts is None:
            self.parts = [("".join(self.prefixes) if node.indented else "", None)]
        self.parts.append((node.text, node.cost))

    def visit_codeblock(self, node):
        for element in node.elements:
            element.accept(self)

    def close_line(self):
        parts = self.parts
        while parts and parts[-1][1] is None and not parts[-1][0].rstrip():
            parts.pop()
        if parts and parts[-1][1] is None:
            parts[-1] = (parts[-1][0].rstrip(), None)
        text = "".join(text for text, _ in parts)
        cost = sum(self.measure(text) if cost is None else cost for text, cost in parts)
        self.lines.append((text, cost))
        self.parts = None

    def resolve(self, node):
        self.reset()
        node.accept(self)
        if self.parts is not None:
            self.close_line()
        return NEWLINE.join(text for text, _ in self.lines)

    @property
    def length(self):
        """What the resolved text weighs once its trailing blank lines are
        gone — the weight of `resolve(...).rstrip()`."""
        lines = self.lines[:]
        while lines and not lines[-1][0]:
            lines.pop()
        return sum(cost for _, cost in lines) + max(len(lines) - 1, 0)


def codeblock_from_string(content: str, indent_size: int = 2) -> CodeBlock:
    block = CodeBlock()
    lines = content.strip("\n").splitlines()

    current_indent_level = 0

    for line in lines:
        raw_line = line.rstrip()
        leading_spaces = len(line) - len(line.lstrip())
        line_indent_level = leading_spaces // indent_size

        # Adjust indent/dedent
        while current_indent_level < line_indent_level:
            block.add_indent()
            current_indent_level += 1
        while current_indent_level > line_indent_level:
            block.add_dedent()
            current_indent_level -= 1

        if raw_line.strip() == "":
            block.add_newline()
        else:
            block.add_text(raw_line.lstrip())
            block.add_newline()

    # Close any remaining indentation
    while current_indent_level > 0:
        block.add_dedent()
        current_indent_level -= 1

    return block
