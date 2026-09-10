import pytest

from inkletter.codeblock import CodeBlock, CodeBlockResolver


def test_simple_function():
    cb = CodeBlock()
    cb.add_text("def foo():")
    cb.add_newline()
    cb.add_indent()
    cb.add_text("print('Hello')")
    cb.add_newline()
    cb.add_dedent()

    resolver = CodeBlockResolver()
    result = resolver.resolve(cb)

    expected = """\
def foo():
  print('Hello')"""
    assert result == expected


def test_nested_functions():
    cb = CodeBlock()
    cb.add_text("def outer():")
    cb.add_newline()
    cb.add_indent()
    cb.add_text("def inner():")
    cb.add_newline()
    cb.add_indent()
    cb.add_text("return 42")
    cb.add_newline()
    cb.add_dedent()
    cb.add_dedent()

    resolver = CodeBlockResolver()
    result = resolver.resolve(cb)

    expected = """\
def outer():
  def inner():
    return 42"""
    assert result == expected


def test_multiple_statements_same_indent():
    cb = CodeBlock()
    cb.add_text("x = 1")
    cb.add_newline()
    cb.add_text("y = 2")
    cb.add_newline()
    cb.add_text("z = x + y")
    cb.add_newline()

    resolver = CodeBlockResolver()
    result = resolver.resolve(cb)

    expected = """\
x = 1
y = 2
z = x + y"""
    assert result == expected


def test_indent_dedent_behavior():
    cb = CodeBlock()
    cb.add_text("if condition:")
    cb.add_newline()
    cb.add_indent()
    cb.add_text("do_something()")
    cb.add_newline()
    cb.add_dedent()
    cb.add_text("print('Done')")
    cb.add_newline()

    resolver = CodeBlockResolver()
    result = resolver.resolve(cb)

    expected = """\
if condition:
  do_something()
print('Done')"""
    assert result == expected


def test_empty_codeblock():
    cb = CodeBlock()

    resolver = CodeBlockResolver()
    result = resolver.resolve(cb)

    expected = ""  # Nothing generated
    assert result == expected


def test_consecutive_newlines():
    cb = CodeBlock()
    cb.add_text("first line")
    cb.add_newline()
    cb.add_newline()
    cb.add_text("second line")
    cb.add_newline()

    resolver = CodeBlockResolver()
    result = resolver.resolve(cb)

    expected = """\
first line

second line"""
    assert result == expected


def test_error_on_invalid_dedent():
    cb = CodeBlock()
    cb.add_dedent()

    resolver = CodeBlockResolver()

    with pytest.raises(ValueError, match="Cannot dedent below zero"):
        resolver.resolve(cb)


# --- Weighing ---
#
# The resolver sums a cost as it lays the lines out: what a fragment
# declared, or `measure` of what it says — `len` unless told otherwise.


def test_the_weight_is_the_length_by_default():
    block = CodeBlock()
    block.add_text("hello")
    block.add_newline()
    block.add_indent()
    block.add_text("world")
    resolver = CodeBlockResolver()
    assert resolver.resolve(block) == "hello\n  world"
    assert resolver.length == len("hello\n  world")


def test_a_declared_cost_replaces_the_measure():
    block = CodeBlock()
    block.add_text("a ")
    block.add_text("@[long marker|Acme]", cost=4)
    resolver = CodeBlockResolver()
    assert resolver.resolve(block) == "a @[long marker|Acme]"
    assert resolver.length == 2 + 4


def test_the_measure_is_the_caller_s_unit():
    block = CodeBlock()
    block.add_text("👋")
    resolver = CodeBlockResolver(measure=lambda text: len(text.encode("utf-16-le")) // 2)
    resolver.resolve(block)
    assert resolver.length == 2


def test_a_prefix_is_any_string():
    block = CodeBlock()
    block.add_indent("> ")
    block.add_text("quoted")
    block.add_newline()
    block.add_newline()
    block.add_text("still")
    block.add_dedent()
    resolver = CodeBlockResolver()
    assert resolver.resolve(block) == "> quoted\n>\n> still"
    assert resolver.length == len("> quoted\n>\n> still")


def test_trailing_whitespace_costs_nothing():
    block = CodeBlock()
    block.add_text("text   ")
    block.add_newline()
    block.add_newline()
    resolver = CodeBlockResolver()
    assert resolver.resolve(block) == "text\n"
    assert resolver.length == len("text")
