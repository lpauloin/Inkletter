INDENT_SIZE = 2  # Number of spaces per indent level
NEWLINE = "\n"  # Newline character


# Base class for all elements
class CodeElement:
    def accept(self, visitor):
        raise NotImplementedError()


# Concrete element classes
class Indent(CodeElement):
    def accept(self, visitor):
        return visitor.visit_indent(self)


class Dedent(CodeElement):
    def accept(self, visitor):
        return visitor.visit_dedent(self)


class Newline(CodeElement):
    def accept(self, visitor):
        return visitor.visit_newline(self)


class TextElement(CodeElement):
    def __init__(self, text, indented=True):
        self.text = text
        self.indented = indented

    def accept(self, visitor):
        return visitor.visit_text(self)


# The main CodeBlock class
class CodeBlock(CodeElement):
    def __init__(self):
        self.elements = []

    def add_indent(self):
        self.elements.append(Indent())

    def add_dedent(self):
        self.elements.append(Dedent())

    def add_text(self, text, indented=True):
        self.elements.append(TextElement(text, indented=indented))

    def add_newline(self):
        self.elements.append(Newline())

    def add_codeblock(self, cb):
        self.elements.append(cb)

    def accept(self, visitor):
        return visitor.visit_codeblock(self)


# Visitor to resolve the CodeBlock to a string
class CodeBlockResolver:
    def __init__(self, indent_size=INDENT_SIZE, starting_indent=0):
        self.indent_size = indent_size
        self.starting_indent = starting_indent
        self.current_indent = starting_indent
        self.lines = []
        self.current_line = None

    def visit_indent(self, node):
        self.current_indent += 1

    def visit_dedent(self, node):
        if self.current_indent == 0:
            raise ValueError("Cannot dedent below zero")
        self.current_indent -= 1

    def visit_newline(self, node):
        self.lines.append(self.current_line or "")
        self.current_line = None

    def visit_text(self, node):
        if self.current_line is None:
            self.current_line = (
                " " * (self.current_indent * self.indent_size) if node.indented else ""
            )
        self.current_line += node.text

    def visit_codeblock(self, node):
        for element in node.elements:
            element.accept(self)

    def resolve(self, node):
        self.current_indent = self.starting_indent
        self.lines = []
        self.current_line = None
        node.accept(self)
        if self.current_line is not None:
            self.lines.append(self.current_line)
        return NEWLINE.join(l.rstrip() for l in self.lines)


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
