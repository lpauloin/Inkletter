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


def test_a_rule_typed_between_two_lines_still_separates_them():
    assert parse_markdown_to_linkedin("Avant\n***\nAprès") == "Avant\n\nAprès"


def test_a_rule_adds_nothing_to_the_blank_lines_typed_around_it():
    assert parse_markdown_to_linkedin("Avant\n\n\n***\n\n\nAprès") == "Avant\n\n\nAprès"


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


def test_the_blank_lines_after_a_list_are_the_authors():
    assert parse_markdown_to_linkedin("- a\n\n\n> b") == "• a\n\n\n> b"
    assert parse_markdown_to_linkedin("- a\n\nb") == "• a\n\nb"


def test_the_blank_lines_between_the_items_of_a_loose_list_are_the_authors():
    assert parse_markdown_to_linkedin("- Un\n\n- Deux") == "• Un\n\n• Deux"
    assert (
        parse_markdown_to_linkedin("1. Un\n\n\n2. Deux\n3. Trois") == "1. Un\n\n\n2. Deux\n3. Trois"
    )
    assert parse_markdown_to_linkedin("- [ ] Un\n\n- [x] Deux") == "[ ] Un\n\n[x] Deux"
    # nested: the blank line carries no indent
    assert (
        parse_markdown_to_linkedin("- Un\n  - a\n\n  - b\n- Deux") == "• Un\n  • a\n\n  • b\n• Deux"
    )


def test_a_line_typed_after_a_list_follows_it_without_a_blank_line():
    assert parse_markdown_to_linkedin("- Étapes\nAprès") == "• Étapes\nAprès"
    assert parse_markdown_to_linkedin("1. Étapes\nAprès") == "1. Étapes\nAprès"
    assert parse_markdown_to_linkedin("- [ ] Étapes\nAprès") == "[ ] Étapes\nAprès"


def test_a_list_typed_after_a_line_follows_it_without_a_blank_line():
    assert (
        parse_markdown_to_linkedin("Voici :\n- Un point\nMerci.") == "Voici :\n• Un point\nMerci."
    )


def test_lists_of_two_kinds_typed_line_after_line_stay_line_after_line():
    assert parse_markdown_to_linkedin("- Un\n1. Deux\n- Trois") == "• Un\n1. Deux\n• Trois"
    assert parse_markdown_to_linkedin("1. Un\n- [ ] Deux\n1. Trois") == "1. Un\n[ ] Deux\n1. Trois"


def test_the_blank_lines_a_document_opens_or_ends_on_separate_nothing():
    # the platform trims them before counting, so keeping them would make
    # our count disagree with theirs
    assert parse_markdown_to_linkedin("\n\n\nUn") == "Un"
    assert parse_markdown_to_linkedin("Du texte.  \n\n\n") == "Du texte."


# --- What the platform counts for them ---


def test_a_blank_line_costs_the_newline_it_is(measured):
    assert measured("Un\n\n\nDeux") == measured("Un\n\nDeux") + 1
    assert measured("Un\n\n\n\nDeux") == measured("Un\n\nDeux") + 2


def test_a_run_a_document_opens_on_costs_nothing(measured):
    assert measured("\n\n\nUn") == measured("Un")


def test_the_blank_lines_after_an_indented_code_block_are_the_authors():
    actual = parse_markdown_to_linkedin("Avant :\n\n    code\n\nAprès", max_length=None)
    print(actual)
    assert actual == "Avant :\n\n    code\n\nAprès"


def test_a_heading_right_under_a_quote_is_its_own_line():
    actual = parse_markdown_to_linkedin("> a\n## b", max_length=None)
    print(actual)
    assert actual == "> a\nb"


def test_a_list_right_under_a_quote_follows_it():
    actual = parse_markdown_to_linkedin("> Citée\n- un point", max_length=None)
    print(actual)
    assert actual == "> Citée\n• un point"


def test_a_rule_inside_a_list_item_draws_no_dashes():
    actual = parse_markdown_to_linkedin("- a\n\n  ***\n\n  b", max_length=None)
    print(actual)
    assert "---" not in actual


def test_a_loose_item_keeps_the_blank_lines_between_its_blocks():
    assert parse_markdown_to_linkedin("- a\n\n  para\n\n- b") == "• a\n\n  para\n\n• b"


def test_a_row_of_images_writes_one_per_line():
    assert (
        parse_markdown_to_linkedin("![a](https://e.fr/a.png) ![b](https://e.fr/b.png)")
        == "![a](https://e.fr/a.png)\n![b](https://e.fr/b.png)"
    )


def test_an_image_after_its_text_stays_after_it():
    assert (
        parse_markdown_to_linkedin("Texte avant ![a](https://e.fr/a.png)")
        == "Texte avant\n\n![a](https://e.fr/a.png)"
    )


def test_a_quote_opening_an_item_marks_its_first_line_too():
    assert parse_markdown_to_linkedin("- > a\n  > b") == "• > a\n  > b"


def test_the_breaks_a_paragraph_opens_or_ends_on_separate_nothing():
    assert parse_markdown_to_linkedin("\\\na") == "a"


def test_an_item_whose_first_block_writes_nothing_keeps_its_words_on_its_marker():
    assert parse_markdown_to_linkedin("- <!-- c -->\n  a") == "• a"
    assert parse_markdown_to_linkedin("- <!-- c -->\n\n  a\n\n- b") == "• a\n\n• b"


def test_a_block_showing_nothing_leaves_no_mark():
    assert parse_markdown_to_linkedin("- >\n\n  a") == "• a"
    assert parse_markdown_to_linkedin("- #\n\n  a") == "• a"
    assert parse_markdown_to_linkedin("a\n\n> <!-- c -->\n\nb") == "a\n\nb"
