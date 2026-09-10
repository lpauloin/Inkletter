from inkletter.codeblock import CodeBlockResolver, codeblock_from_string


def resolve_block(block, indent_size=2):
    resolver = CodeBlockResolver(indent_size=indent_size)
    return resolver.resolve(block)


def test_codeblock_simple_code():
    content = """\
def foo():
  return 42"""

    block = codeblock_from_string(content)
    result = resolve_block(block)

    assert result == content


def test_codeblock_multiple_indent_levels():
    content = """\
def outer():
  def inner():
    return 42"""

    block = codeblock_from_string(content)
    result = resolve_block(block)

    assert result == content


def test_codeblock_empty_lines():
    content = """\
def foo():

  return 42"""

    block = codeblock_from_string(content)
    result = resolve_block(block)

    assert result == content


def test_codeblock_only_empty_lines():
    content = """

"""

    block = codeblock_from_string(content)
    result = resolve_block(block)

    assert result == ""


def test_codeblock_no_indentation():
    content = """\
print('Hello')
print('World')"""

    block = codeblock_from_string(content)
    result = resolve_block(block)

    assert result == content


def test_codeblock_mixed_indent_and_unindented_lines():
    content = """\
print('Start')
  print('Indented')
print('End')"""

    block = codeblock_from_string(content)
    result = resolve_block(block)

    assert result == content


def test_codeblock_custom_indent_size():
    content = """\
def foo():
    print('Hello')
    print('World')"""

    block = codeblock_from_string(content, indent_size=4)
    result = resolve_block(block, indent_size=4)

    assert result == content
