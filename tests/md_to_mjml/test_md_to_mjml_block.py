import pytest

from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body


# --- Paragraph ---


def test_paragraph():
    markdown_input = """This is a paragraph."""
    expected_content = """<mj-text>
  This is a paragraph.
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Headings ---


@pytest.mark.parametrize(
    "markdown_input, level, text",
    [
        ("# Heading 1", 1, "Heading 1"),
        ("## Heading 2", 2, "Heading 2"),
        ("### Heading 3", 3, "Heading 3"),
        ("#### Heading 4", 4, "Heading 4"),
        ("##### Heading 5", 5, "Heading 5"),
        ("###### Heading 6", 6, "Heading 6"),
    ],
)
def test_headings(markdown_input, level, text):
    expected_content = f"""\
<mj-text>
  <h{level}>{text}</h{level}>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


@pytest.mark.parametrize(
    "markdown_input, expected_content",
    [
        (
            "# This is a **bold** heading",
            "<mj-text>\n"
            "  <h1>This is a <strong>bold</strong> heading</h1>\n"
            "</mj-text>",
        ),
        (
            "## This is an *italic* heading",
            "<mj-text>\n"
            "  <h2>This is an <em>italic</em> heading</h2>\n"
            "</mj-text>",
        ),
        (
            "### This is a ~~strikethrough~~ heading",
            "<mj-text>\n"
            "  <h3>This is a <del>strikethrough</del> heading</h3>\n"
            "</mj-text>",
        ),
        (
            "#### This is a `code` heading",
            "<mj-text>\n"
            "  <h4>This is a <code>code</code> heading</h4>\n"
            "</mj-text>",
        ),
        (
            "##### This is a [link](https://example.com)",
            "<mj-text>\n"
            '  <h5>This is a <a href="https://example.com">link</a></h5>\n'
            "</mj-text>",
        ),
    ],
)
def test_headings_with_inlines(markdown_input, expected_content):
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    assert actual == expected


# --- Blockquote ---


def test_blockquote():
    markdown_input = """> This is a quote."""
    expected_content = """\
<mj-text>
  <blockquote>
    This is a quote.
  </blockquote>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Thematic Break (horizontal rule) ---


def test_thematic_break():
    markdown_input = """---"""
    expected_content = """<mj-divider border-color="#cccccc" border-width="1px"/>"""
    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


# --- Code Block ---


def test_block_code():
    markdown_input = """\
```python
print("Hello")
def greet(name):
  return f"Hello, {name}!"
```"""
    expected = """\
<mjml>
  <mj-body>
    <mj-section>
      <mj-column>
        <mj-text>
          <pre>
print(&quot;Hello&quot;)
def greet(name):
  return f&quot;Hello, {name}!&quot;
          </pre>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""
    actual = parse_markdown_to_mjml(markdown_input)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_block_code_with_html():
    markdown_input = """\
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sample Page</title>
</head>
<body>
  <h1>Hello, world!</h1>
  <p>This is a paragraph of HTML code.</p>
</body>
</html>
```"""
    expected = """\
<mjml>
  <mj-body>
    <mj-section>
      <mj-column>
        <mj-text>
          <pre>
&lt;!DOCTYPE html&gt;
&lt;html lang=&quot;en&quot;&gt;
&lt;head&gt;
  &lt;meta charset=&quot;UTF-8&quot;&gt;
  &lt;title&gt;Sample Page&lt;/title&gt;
&lt;/head&gt;
&lt;body&gt;
  &lt;h1&gt;Hello, world!&lt;/h1&gt;
  &lt;p&gt;This is a paragraph of HTML code.&lt;/p&gt;
&lt;/body&gt;
&lt;/html&gt;
          </pre>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""
    actual = parse_markdown_to_mjml(markdown_input)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected
