"""The three styles, and every way they meet.

Bold, italic and strikethrough become `<strong>`, `<em>` and `<s>`. What
these tests pin is how the styles combine — in any nesting order, whatever
marks spell them — and that a style around anything keeps that thing whole:
a link, its address, a hashtag, a mention, a code span, and the blocks a
style lives in.
"""

import re
from itertools import permutations

import pytest

from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment

TAGS = {"bold": "strong", "italic": "em", "strike": "s"}

MARKS = {
    "*": {"bold": "**", "italic": "*", "strike": "~~"},
    "_": {"bold": "__", "italic": "_", "strike": "~~"},
}


def nested(word, order, family):
    """`word` wrapped in the marks of `order`, outermost first."""
    opening = "".join(MARKS[family][style] for style in order)
    closing = "".join(MARKS[family][style] for style in reversed(order))
    return f"{opening}{word}{closing}"


def wrapping(html, word):
    """The tags that open right before `word` in `html`, and whether each
    closes after it, innermost last — the styles around the word, whatever
    order the parser settled on where the marks leave it open (`***word***`
    reads as italic around bold or bold around italic alike)."""
    before, _, after = html.partition(word)
    opened = re.findall(r"<(strong|em|s)>", before.rsplit(" ", 1)[-1])
    closed = re.findall(r"</(strong|em|s)>", after.split(" ", 1)[0])
    return opened, closed


ORDERS = [order for size in (1, 2, 3) for order in permutations(("bold", "italic", "strike"), size)]


# --- Every combination, in every order, with either family of marks ---


@pytest.mark.parametrize("family", ["*", "_"])
@pytest.mark.parametrize("order", ORDERS)
def test_styles_combine_whatever_is_outside(order, family):
    actual = parse_markdown_to_html_fragment(f"a {nested('word', order, family)} here")
    print(actual)
    opened, closed = wrapping(actual, "word")
    assert sorted(opened) == sorted(TAGS[style] for style in order)
    assert closed == list(reversed(opened))
    assert actual.startswith("<p>a <") and actual.endswith("> here</p>")


def test_marks_the_parser_can_tell_apart_nest_as_written():
    actual = parse_markdown_to_html_fragment("a **bold ~~struck *all*~~** here")
    print(actual)
    assert actual == "<p>a <strong>bold <s>struck <em>all</em></s></strong> here</p>"


def test_marks_of_both_families_mix():
    actual = parse_markdown_to_html_fragment("**bold and _italic_ inside**")
    print(actual)
    assert actual == "<p><strong>bold and <em>italic</em> inside</strong></p>"


def test_a_style_closing_inside_another_keeps_the_rest():
    actual = parse_markdown_to_html_fragment("*one **two** three*")
    print(actual)
    assert actual == "<p><em>one <strong>two</strong> three</em></p>"


def test_the_three_styles_at_once():
    actual = parse_markdown_to_html_fragment("***~~all~~***")
    print(actual)
    assert "<s>all</s>" in actual and "<strong>" in actual and "<em>" in actual


def test_a_style_spanning_a_line_break():
    actual = parse_markdown_to_html_fragment("**first\nsecond**")
    print(actual)
    assert actual == "<p><strong>first<br>second</strong></p>"


# --- A style around a thing keeps the thing whole ---


@pytest.mark.parametrize("order", ORDERS)
def test_a_link_inside_a_style_keeps_its_address(order):
    actual = parse_markdown_to_html_fragment(
        f"see {nested('[the guide](https://exemple.fr/g)', order, '*')} now"
    )
    print(actual)
    assert '<a href="https://exemple.fr/g">the guide</a>' in actual


def test_a_style_inside_a_link_label():
    actual = parse_markdown_to_html_fragment("[the **full** ~~old~~ guide](https://exemple.fr)")
    print(actual)
    assert (
        actual
        == '<p><a href="https://exemple.fr">the <strong>full</strong> <s>old</s> guide</a></p>'
    )


def test_a_bold_link_among_words_is_a_bold_link_not_a_button():
    actual = parse_markdown_to_html_fragment("Read **[the study](https://exemple.fr)** today.")
    print(actual)
    assert (
        actual == '<p>Read <strong><a href="https://exemple.fr">the study</a></strong> today.</p>'
    )


# --- A hashtag is text, whatever style is around it ---


@pytest.mark.parametrize(
    ("marks", "tags"),
    [
        ("**", ["strong"]),
        ("*", ["em"]),
        ("~~", ["s"]),
        ("***", ["em", "strong"]),
        ("**~~", ["s", "strong"]),
    ],
)
def test_a_hashtag_inside_any_style_is_written_as_is(marks, tags):
    closing = marks[::-1]
    actual = parse_markdown_to_html_fragment(f"{marks}#marketing{closing}")
    print(actual)
    opened, closed = wrapping(actual, "#marketing")
    assert sorted(opened) == tags
    assert closed == list(reversed(opened))


def test_the_words_around_a_hashtag_keep_their_style():
    actual = parse_markdown_to_html_fragment("**Parlons #marketing B2B**")
    print(actual)
    assert actual == "<p><strong>Parlons #marketing B2B</strong></p>"


def test_an_accented_hashtag_is_one_too():
    actual = parse_markdown_to_html_fragment("*#étude2026 et #équipe_rh*")
    print(actual)
    assert actual == "<p><em>#étude2026 et #équipe_rh</em></p>"


def test_what_is_not_a_hashtag_is_styled_text():
    actual = parse_markdown_to_html_fragment("**#2026 C#**")
    print(actual)
    assert actual == "<p><strong>#2026 C#</strong></p>"


def test_a_hashtag_after_punctuation_is_one():
    actual = parse_markdown_to_html_fragment("**(#marketing)**")
    print(actual)
    assert actual == "<p><strong>(#marketing)</strong></p>"


@pytest.mark.parametrize("tag", ["#équipe_rh", "#a_b_c", "#mot_clé_2026"])
def test_a_hashtag_the_parser_splits_on_underscores_is_still_one(tag):
    actual = parse_markdown_to_html_fragment(f"*{tag} ici*")
    print(actual)
    assert actual == f"<p><em>{tag} ici</em></p>"


def test_a_hashtag_does_not_run_into_the_next_line():
    actual = parse_markdown_to_html_fragment("**#tag**\nsuite **gras**")
    print(actual)
    assert actual == "<p><strong>#tag</strong><br>suite <strong>gras</strong></p>"


def test_a_hashtag_does_not_run_into_the_next_paragraph():
    actual = parse_markdown_to_html_fragment("**#tag**\n\n**gras**")
    print(actual)
    assert actual == "<p><strong>#tag</strong></p><p><strong>gras</strong></p>"


def test_a_hashtag_does_not_run_into_the_next_item():
    actual = parse_markdown_to_html_fragment("- **#un**\n- **deux**")
    print(actual)
    assert actual == "<ul><li><strong>#un</strong></li><li><strong>deux</strong></li></ul>"


def test_a_mention_inside_a_style_is_its_name():
    actual = parse_markdown_to_html_fragment("**Bravo [Kehaia](urn:li:organization:1)**")
    print(actual)
    assert actual == "<p><strong>Bravo Kehaia</strong></p>"


def test_a_code_span_inside_a_style():
    actual = parse_markdown_to_html_fragment("**run `make < x`**")
    print(actual)
    assert actual == "<p><strong>run <code>make &lt; x</code></strong></p>"


def test_escaped_text_inside_a_style():
    actual = parse_markdown_to_html_fragment("*1 < 2 & 3*")
    print(actual)
    assert actual == "<p><em>1 &lt; 2 &amp; 3</em></p>"


def test_an_emoji_inside_a_style():
    actual = parse_markdown_to_html_fragment("~~bientôt 🎉~~")
    print(actual)
    assert actual == "<p><s>bientôt 🎉</s></p>"


def test_marks_that_style_nothing_stay_text():
    actual = parse_markdown_to_html_fragment("2 * 3 * 4 and a_b_c")
    print(actual)
    assert actual == "<p>2 * 3 * 4 and a_b_c</p>"


# --- Styles in every block ---


def test_styles_in_a_heading():
    actual = parse_markdown_to_html_fragment("## A **bold** and *calm* title")
    print(actual)
    assert actual == "<h2>A <strong>bold</strong> and <em>calm</em> title</h2>"


def test_styles_in_list_items():
    actual = parse_markdown_to_html_fragment("- **one**\n- *two*\n- ~~three~~")
    print(actual)
    assert (
        actual == "<ul><li><strong>one</strong></li><li><em>two</em></li><li><s>three</s></li></ul>"
    )


def test_styles_in_an_ordered_list_with_a_link():
    actual = parse_markdown_to_html_fragment(
        "1. read **[the study](https://exemple.fr)**\n2. share it"
    )
    print(actual)
    assert (
        actual
        == '<ol><li>read <strong><a href="https://exemple.fr">the study</a></strong></li><li>share it</li></ol>'
    )


def test_styles_in_a_task_list():
    actual = parse_markdown_to_html_fragment("- [x] **done**\n- [ ] *to do*")
    print(actual)
    assert actual == "<ul><li>☑ <strong>done</strong></li><li>☐ <em>to do</em></li></ul>"


def test_styles_in_a_quote():
    actual = parse_markdown_to_html_fragment("> a **bold** quote\n> on *two* lines")
    print(actual)
    assert (
        actual
        == "<blockquote><p>a <strong>bold</strong> quote<br>on <em>two</em> lines</p></blockquote>"
    )


def test_styles_in_table_cells():
    actual = parse_markdown_to_html_fragment(
        "| **Head** | *Other* |\n|---|---|\n| ~~old~~ | `code` |"
    )
    print(actual)
    assert "<th><strong>Head</strong></th><th><em>Other</em></th>" in actual
    assert "<td><s>old</s></td><td><code>code</code></td>" in actual


def test_styles_in_a_nested_list():
    actual = parse_markdown_to_html_fragment("- **a**\n  - *a1*")
    print(actual)
    assert actual == "<ul><li><strong>a</strong><ul><li><em>a1</em></li></ul></li></ul>"


def test_no_style_reaches_a_code_block():
    actual = parse_markdown_to_html_fragment("```\n**not bold** *nor italic*\n```")
    print(actual)
    assert actual == "<pre><code>**not bold** *nor italic*\n</code></pre>"


# --- Marks that do not close, or style nothing ---


@pytest.mark.parametrize(
    "markdown_text",
    ["**not closed", "*not closed", "~~not closed", "**bold *mixed** end*", "`not closed"],
)
def test_a_mark_that_never_closes_leaves_balanced_tags(markdown_text):
    actual = parse_markdown_to_html_fragment(markdown_text)
    print(actual)
    for tag in ("strong", "em", "s", "code", "p"):
        assert actual.count(f"<{tag}>") == actual.count(f"</{tag}>")


@pytest.mark.parametrize("markdown_text", ["****", "**  **", "~~~~", "__"])
def test_marks_around_nothing(markdown_text):
    actual = parse_markdown_to_html_fragment(markdown_text)
    print(actual)
    for tag in ("strong", "em", "s"):
        assert actual.count(f"<{tag}>") == actual.count(f"</{tag}>")


def test_escaped_marks_are_text():
    actual = parse_markdown_to_html_fragment(
        "\\*not italic\\* and \\#not_a_heading and \\[not](a link)"
    )
    print(actual)
    assert actual == "<p>*not italic* and #not_a_heading and [not](a link)</p>"


def test_deep_nesting_stays_balanced():
    actual = parse_markdown_to_html_fragment("***~~a **b *c ~~d~~ c* b** a~~***")
    print(actual)
    assert actual == (
        "<p><em><strong><s>a <strong>b <em>c <s>d</s> c</em> b</strong> a</s></strong></em></p>"
    )


# --- Blocks inside blocks ---
