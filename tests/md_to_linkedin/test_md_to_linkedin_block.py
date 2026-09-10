from inkletter.md_to_linkedin import parse_markdown_to_linkedin

# --- Headings ---


def test_a_heading_is_a_line_without_an_underline():
    # a row of equals signs is a convention of plain-text mail; a feed
    # would show it as what it is, forty characters of noise
    actual = parse_markdown_to_linkedin("# Notre étude\n\nDu texte.")
    print(actual)
    assert actual == "Notre étude\n\nDu texte."


def test_every_heading_level_reads_the_same():
    assert parse_markdown_to_linkedin("# Un\n\n###### Six") == "Un\n\nSix"


# --- Lists ---
#
# The platform refuses list markup, so the marker is written in the text.
# The three forms cost the same, `• ` being two units like `1. `.


def test_a_bullet_list_gets_a_real_bullet():
    assert parse_markdown_to_linkedin("- une\n- deux") == "• une\n• deux"


def test_a_numbered_list_keeps_its_numbers():
    assert parse_markdown_to_linkedin("1. une\n2. deux") == "1. une\n2. deux"


def test_a_numbered_list_starts_where_it_says():
    assert parse_markdown_to_linkedin("3. trois\n4. quatre") == "3. trois\n4. quatre"


def test_a_nested_list_is_indented():
    assert parse_markdown_to_linkedin("- une\n  - dedans\n- deux") == "• une\n  • dedans\n• deux"


def test_a_task_list_keeps_its_boxes():
    assert parse_markdown_to_linkedin("- [x] fait\n- [ ] à faire") == "[x] fait\n[ ] à faire"


# --- Tables ---


def test_a_table_is_flattened_row_by_row():
    # a proportional font undoes any alignment, so padded columns would
    # arrive as ragged text
    actual = parse_markdown_to_linkedin("| Canal | Part |\n|---|---|\n| Email | 42 % |")
    print(actual)
    assert actual == "Canal — Part\nEmail — 42 %"


# --- Horizontal rules ---


def test_a_horizontal_rule_becomes_a_blank_line():
    assert parse_markdown_to_linkedin("Avant\n\n---\n\nAprès") == "Avant\n\nAprès"


# --- No buttons ---
#
# A feed draws none, so the tree is built without any: a lone bold link
# stays a bold link, renders as the line it is made of, and reaches the
# factory as bold — which is how a caller tells the call to action apart.


def test_a_lone_bold_link_is_a_line():
    actual = parse_markdown_to_linkedin("**[Réserver](https://exemple.fr/rdv)**")
    print(actual)
    assert actual == "Réserver : https://exemple.fr/rdv"


def test_a_lone_bold_link_reaches_the_factory_as_bold():
    from inkletter.shortener import URLFactory

    class Telling(URLFactory):
        seen = []

        def rewrite_link(self, url, is_button=False, is_bold=False):
            self.seen.append((url, is_button, is_bold))
            return url

    parse_markdown_to_linkedin(
        "Voir [ici](https://a.test).\n\n**[Réserver](https://b.test)**", url_factory=Telling()
    )
    assert Telling.seen == [("https://a.test", False, False), ("https://b.test", False, True)]


# --- Everything else the text output already did ---


def test_a_quote_keeps_its_marker():
    assert parse_markdown_to_linkedin("> Une citation.") == "> Une citation."


def test_a_code_block_keeps_its_indentation():
    assert parse_markdown_to_linkedin("```python\nprint(1)\n```") == "    print(1)"


def test_trailing_whitespace_is_trimmed():
    # the platform trims before counting, so keeping it would make our
    # count disagree with theirs
    assert parse_markdown_to_linkedin("Du texte.  \n\n\n") == "Du texte."
