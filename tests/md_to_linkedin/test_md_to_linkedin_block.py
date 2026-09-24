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


# --- The blank lines an author left ---


def test_a_run_of_blank_lines_is_kept_line_for_line():
    # Markdown reads a run as one paragraph break; a feed is sent what was
    # typed, and an author who spaces their lines out means it
    assert parse_markdown_to_linkedin("Un\n\nDeux") == "Un\n\nDeux"
    assert parse_markdown_to_linkedin("Un\n\n\nDeux") == "Un\n\n\nDeux"
    assert parse_markdown_to_linkedin("Un\n\n\n\n\nDeux") == "Un\n\n\n\n\nDeux"


def test_blank_lines_between_any_two_blocks_are_kept():
    assert parse_markdown_to_linkedin("# Titre\n\n\nUn") == "Titre\n\n\nUn"
    assert parse_markdown_to_linkedin("Un\n\n\n> b") == "Un\n\n\n> b"


def test_a_list_reads_the_blank_lines_that_follow_it_as_its_own():
    # they belong to the list's own parsing — a loose list eats them — so
    # the run between a list and what follows stays the single break
    assert parse_markdown_to_linkedin("- a\n\n\n> b") == "• a\n\n> b"


def test_the_blank_lines_a_document_opens_or_ends_on_separate_nothing():
    # the platform trims them before counting, so keeping them would make
    # our count disagree with theirs
    assert parse_markdown_to_linkedin("\n\n\nUn") == "Un"
    assert parse_markdown_to_linkedin("Du texte.  \n\n\n") == "Du texte."


def test_a_run_of_blank_lines_inside_a_list_leaves_the_items_alone():
    assert parse_markdown_to_linkedin("- a\n\n\n- b") == "• a\n• b"


# --- What the platform counts for them ---


def test_a_blank_line_costs_the_newline_it_is(measured):
    assert measured("Un\n\n\nDeux") == measured("Un\n\nDeux") + 1
    assert measured("Un\n\n\n\nDeux") == measured("Un\n\nDeux") + 2


def test_a_run_a_document_opens_on_costs_nothing(measured):
    assert measured("\n\n\nUn") == measured("Un")
