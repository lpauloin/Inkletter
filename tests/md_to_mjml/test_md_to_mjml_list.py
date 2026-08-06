from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body


def test_unordered_list():
    markdown_input = """\
- Item 1
- Item 2
- Item 3"""
    expected_content = """\
<mj-text>
  <ul>
    <li>
      Item 1
    </li>
    <li>
      Item 2
    </li>
    <li>
      Item 3
    </li>
  </ul>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_ordered_list():
    markdown_input = """\
1. First
2. Second
3. Third"""
    expected_content = """\
<mj-text>
  <ol>
    <li>
      First
    </li>
    <li>
      Second
    </li>
    <li>
      Third
    </li>
  </ol>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_unordered_list_with_inlines():
    markdown_input = """\
- **Bold Item**
- *Italic Item*
- `Code Item`
- [Link Item](https://example.com)
- ~~Strikethrough Item~~"""
    expected_content = """\
<mj-text>
  <ul>
    <li>
      <strong>Bold Item</strong>
    </li>
    <li>
      <em>Italic Item</em>
    </li>
    <li>
      <code>Code Item</code>
    </li>
    <li>
      <a href="https://example.com">Link Item</a>
    </li>
    <li>
      <del>Strikethrough Item</del>
    </li>
  </ul>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_task_list(ast):
    markdown_input = """\
- [x] Checked
- [ ] Not checked
"""

    expected_content = """\
<mj-text>
  <ul style="list-style-type: none;">
    <li>
      ☑ Checked
    </li>
    <li>
      ☐ Not checked
    </li>
  </ul>
</mj-text>
"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_task_list_nested_1(ast):
    markdown_input = """\
- [x] Checked
  1. Checked sub list Item 1
  2. Checked sub list Item 2
- [ ] Not checked
  1. Not checked sub list Item 1
  2. Not checked sub list Item 2
"""

    expected_content = """\
<mj-text>
  <ul style="list-style-type: none;">
    <li>
      ☑ Checked
      <ol>
        <li>
          Checked sub list Item 1
        </li>
        <li>
          Checked sub list Item 2
        </li>
      </ol>
    </li>
    <li>
      ☐ Not checked
      <ol>
        <li>
          Not checked sub list Item 1
        </li>
        <li>
          Not checked sub list Item 2
        </li>
      </ol>
    </li>
  </ul>
</mj-text>
"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_task_list_nested_2(ast):

    markdown_input = """\
1. List Item 1
2. List Item 2
    - [x] Checked
    - [ ] Not checked
    """

    expected_content = """\
<mj-text>
  <ol>
    <li>
      List Item 1
    </li>
    <li>
      List Item 2
      <ul style="list-style-type: none;">
        <li>
          ☑ Checked
        </li>
        <li>
          ☐ Not checked
        </li>
      </ul>
    </li>
  </ol>
</mj-text>
"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_ordered_list_keeps_its_start_number():
    markdown_input = "3. trois\n4. quatre"
    expected_content = """\
<mj-text>
  <ol start="3">
    <li>
      trois
    </li>
    <li>
      quatre
    </li>
  </ol>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_ordered_list_starting_at_one_has_no_start_attribute():
    actual = parse_markdown_to_mjml("1. un\n2. deux")
    print(actual)
    assert "start=" not in actual
