from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body


def test_image():
    markdown_input = """![Alt Text](https://picsum.photos/600/300)"""
    expected_content = """\
<mj-image src="https://picsum.photos/600/300" alt="Alt Text"/>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_image_and_text():
    markdown_input = """\
This is a text.
![Alt Text](https://picsum.photos/600/300)
This is another."""

    expected_content = """\
<mj-text>
  This is a text.
</mj-text>
<mj-image src="https://picsum.photos/600/300" alt="Alt Text"/>
<mj-text>
  This is another.
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_image_in_link():
    markdown_input = "[![Alt](https://picsum.photos/600/300)](https://lien.com)"

    expected_content = """\
<mj-image src="https://picsum.photos/600/300" href="https://lien.com" alt="Alt"/>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_image_in_list():
    markdown_input = "- ![Étoile](https://picsum.photos/600/300) "

    expected_content = """\
<mj-text>
  <ul>
    <li>
      <img src="https://picsum.photos/600/300" alt="Étoile" style="max-width: 100%; height: auto;"/>
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


def test_image_in_blockquote():
    markdown_input = """\
> ![Quote Icon](https://picsum.photos/600/300)
> Citation
> Du grand citateur"""

    expected_content = """\
<mj-text>
  <blockquote>
    <img src="https://picsum.photos/600/300" alt="Quote Icon" style="max-width: 100%; height: auto;"/>
    Citation<br/>
    Du grand citateur
  </blockquote>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_image_in_table():
    markdown_input = """\
| Produit | Image                                   |
|---------|-----------------------------------------|
| Stylo   | ![Stylo](https://picsum.photos/600/300) |"""

    expected_content = """\
<mj-table>
  <tr>
    <th>Produit</th>
    <th>Image</th>
  </tr>
  <tr>
    <td>Stylo</td>
    <td><img src="https://picsum.photos/600/300" alt="Stylo" style="max-width: 100%; height: auto;"/>
    </td>
  </tr>
</mj-table>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_image_in_heading():
    markdown_input = "## Titre ![Icône](https://picsum.photos/600/300)"

    expected_content = """\
<mj-text>
  <h2>Titre <img src="https://picsum.photos/600/300" alt="Icône" style="max-width: 100%; height: auto;"/>
  </h2>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected


def test_image_alt_with_formatting():
    markdown_input = """![*Bold* star](https://picsum.photos/600/300)"""
    expected_content = """\
<mj-image src="https://picsum.photos/600/300" alt="Bold star"/>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected
