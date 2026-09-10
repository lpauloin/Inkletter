from inkletter.md_to_linkedin import parse_markdown_to_linkedin


def test_full_document_covers_every_markdown_element():
    # every construct a post can carry, in one document: headings, the
    # three inline styles, a code span, a bare address, a link, bullet /
    # nested / ordered lists, a quote, a table, a bold link, a mention, an
    # emoji, a hashtag and a horizontal rule
    markdown_input = """\
# Notre étude 2026 est sortie

Un paragraphe avec de l'*italique*, du **gras**, du ~~barré~~, un `code`,
une adresse nue https://exemple.fr/nu et un [lien](https://exemple.fr/lu).

## Ce qu'elle dit

- une puce
- une autre, avec une sous-liste :
  - imbriquée
1. un premier
2. un second

> Une citation sur
> deux lignes.

| Canal | Part |
|-------|------|
| Email | 42 % |

**[Télécharger l'étude](https://exemple.fr/telecharger)**

---

Merci à [Acme](urn:li:organization:12345678) 👋 #étude
"""
    expected = """\
Notre étude 2026 est sortie

Un paragraphe avec de l'italique, du gras, du barré, un code,
une adresse nue https://exemple.fr/nu et un lien : https://exemple.fr/lu.

Ce qu'elle dit

• une puce
• une autre, avec une sous-liste :
  • imbriquée

1. un premier
2. un second

> Une citation sur
> deux lignes.

Canal — Part
Email — 42 %

Télécharger l'étude : https://exemple.fr/telecharger

Merci à @[urn:li:organization:12345678|Acme] 👋 #étude"""

    actual = parse_markdown_to_linkedin(markdown_input)
    print(actual)
    assert actual == expected


def test_a_first_comment_is_a_document_of_its_own():
    # written apart, published apart, counted apart: the same render, and
    # the ceiling of wherever it is published comes in from the caller —
    # Inkletter knows of no first comment. A horizontal rule stays a rule.
    actual = parse_markdown_to_linkedin(
        "Le rapport complet : [ici](https://exemple.fr/rapport)", max_length=1250
    )
    print(actual)
    assert actual == "Le rapport complet : ici : https://exemple.fr/rapport"


def test_an_empty_document_is_an_empty_post():
    assert parse_markdown_to_linkedin("") == ""
