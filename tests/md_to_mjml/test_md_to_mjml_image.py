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
    <th style="border-bottom: 2px solid #e5e7eb; padding: 8px 12px; text-align: left;">Produit</th>
    <th style="border-bottom: 2px solid #e5e7eb; padding: 8px 12px; text-align: left;">Image</th>
  </tr>
  <tr>
    <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">Stylo</td>
    <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;"><img src="https://picsum.photos/600/300" alt="Stylo" style="max-width: 100%; height: auto;"/>
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


def test_image_inside_inline_formatting_is_manual():
    # an mj-image inside a mj-text would leak as an unknown tag
    actual = parse_markdown_to_mjml("**[![alt](https://x.com/i.png)](https://x.com)**")
    print(actual)
    body = actual[actual.find("<mj-body") :]
    assert "mj-image" not in body
    assert (
        '<strong><a href="https://x.com">'
        '<img src="https://x.com/i.png" alt="alt"' in actual.replace("\n", "")
    )


def test_image_inside_emphasis_is_manual():
    actual = parse_markdown_to_mjml("*voici ![ico](https://x.com/i.png) la*")
    body = actual[actual.find("<mj-body") :]
    assert "mj-image" not in body
    assert '<img src="https://x.com/i.png" alt="ico"' in actual


def test_manual_image_link_keeps_its_link():
    # href is not a valid <img> attribute: the anchor must wrap the image
    actual = parse_markdown_to_mjml("- [![alt](https://x.com/i.png)](https://x.com) item")
    print(actual)
    assert "<img" in actual and "href" not in actual.split("<img")[1].split("/>")[0]
    assert '<a href="https://x.com"><img' in actual


def test_manual_image_link_titles_land_on_the_right_tags():
    actual = parse_markdown_to_mjml(
        '- [![alt](https://x.com/i.png "ImgTitle")](https://x.com "LinkTitle")'
    )
    print(actual)
    link_tag = actual.split("<a ")[1].split(">")[0]
    img_tag = actual.split("<img ")[1].split("/>")[0]
    assert 'title="LinkTitle"' in link_tag
    assert 'title="ImgTitle"' in img_tag


def test_manual_image_link_escapes_urls():
    actual = parse_markdown_to_mjml("- [![a](https://x.com/i.png?a=1&b=2)](https://x.com/?c=3&d=4)")
    assert 'href="https://x.com/?c=3&amp;d=4"' in actual
    assert 'src="https://x.com/i.png?a=1&amp;b=2"' in actual


def test_image_in_strong_without_link_is_manual():
    actual = parse_markdown_to_mjml("**![gras](https://x.com/i.png)**")
    body = actual[actual.find("<mj-body") :]
    assert "mj-image" not in body
    assert "<strong><img" in actual.replace("\n", "").replace("  ", "")


def test_linked_image_in_heading_keeps_anchor():
    actual = parse_markdown_to_mjml("# [![i](https://x.com/i.png)](https://x.com)")
    print(actual)
    body = actual[actual.find("<mj-body") :]
    assert "mj-image" not in body
    assert '<a href="https://x.com"><img' in actual


def test_linked_image_in_table_cell_keeps_anchor():
    actual = parse_markdown_to_mjml("| A |\n|---|\n| [![i](https://x.com/i.png)](https://x.com) |")
    print(actual)
    assert "mj-image" not in actual.split("<mj-table>")[1]
    assert '<a href="https://x.com"><img' in actual


def test_bold_image_link_snapshot():
    markdown_input = "**[![alt](https://x.com/i.png)](https://x.com)**"

    expected_content = """\
<mj-text>
  <strong><a href="https://x.com"><img src="https://x.com/i.png" alt="alt" style="max-width: 100%; height: auto;"/></a></strong>
</mj-text>"""

    actual = parse_markdown_to_mjml(markdown_input)
    expected = wrap_mjml_body(expected_content)

    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected
