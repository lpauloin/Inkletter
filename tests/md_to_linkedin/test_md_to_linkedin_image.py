from inkletter.md_to_linkedin import parse_markdown_to_linkedin

# Images are not supported: a post carries its visual beside the text,
# never inside it. One written in the document is left exactly as it was
# written — nothing is invented for it, and nothing is lost either.


def test_an_image_stays_as_written():
    actual = parse_markdown_to_linkedin("![La couverture](https://exemple.fr/c.png)")
    print(actual)
    assert actual == "![La couverture](https://exemple.fr/c.png)"


def test_a_clickable_image_stays_as_written():
    actual = parse_markdown_to_linkedin(
        "[![Bannière](https://exemple.fr/b.png)](https://exemple.fr/offre)"
    )
    print(actual)
    assert actual == "[![Bannière](https://exemple.fr/b.png)](https://exemple.fr/offre)"


def test_an_image_beside_text_keeps_both():
    actual = parse_markdown_to_linkedin("![Jean](https://exemple.fr/j.png) Jean nous rejoint.")
    print(actual)
    assert actual == "![Jean](https://exemple.fr/j.png)\n\nJean nous rejoint."
