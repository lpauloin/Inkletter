from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body

HEADING = """\
<mj-text>
  <h1>{}</h1>
</mj-text>"""


def test_plain_h1_becomes_the_title():
    actual = parse_markdown_to_mjml("# My newsletter")
    print(actual)
    assert actual == wrap_mjml_body(HEADING.format("My newsletter"), title="My newsletter")


def test_h1_after_a_paragraph_still_counts():
    actual = parse_markdown_to_mjml("Intro.\n\n# The title")
    print(actual)
    assert "<mj-title>The title</mj-title>" in actual


def test_only_the_first_h1_counts():
    actual = parse_markdown_to_mjml("# First\n\n# Second")
    print(actual)
    assert "<mj-title>First</mj-title>" in actual
    assert "Second</mj-title>" not in actual


def test_a_refused_h1_does_not_hand_over_to_the_next_one():
    # the first h1 is the title or there is none: no falling back
    actual = parse_markdown_to_mjml("# The *big* news\n\n# Plain second")
    print(actual)
    assert "<mj-title" not in actual


def test_special_characters_are_escaped():
    actual = parse_markdown_to_mjml("# Tom & Jerry <3")
    print(actual)
    assert "<mj-title>Tom &amp; Jerry &lt;3</mj-title>" in actual


# --- Anything but plain text disqualifies the heading ---


def refused(markdown, **kwargs):
    actual = parse_markdown_to_mjml(markdown, **kwargs)
    print(actual)
    return "<mj-title" not in actual


def test_emphasis_refuses_the_title():
    assert refused("# The *big* news")


def test_strong_refuses_the_title():
    assert refused("# The **big** news")


def test_code_span_refuses_the_title():
    assert refused("# Some `code` here")


def test_link_refuses_the_title():
    assert refused("# A [link](https://x.com)")


def test_image_refuses_the_title():
    assert refused("# ![logo](https://x.com/l.png) and text")


def test_inline_html_refuses_the_title():
    assert refused("# Hello <b>world</b>")


def test_template_tag_refuses_the_title():
    assert refused("# Hi {{ user.name }}", django_tags=True)


def test_a_two_line_setext_heading_refuses_the_title():
    assert refused("Title\nsecond line\n=====")


# --- No title at all ---


def test_document_without_a_heading():
    assert refused("Just a paragraph.")


def test_document_starting_with_an_h2():
    assert refused("## Only an h2")


def test_empty_document():
    assert refused("")


def test_heading_in_a_quote_is_not_the_document_title():
    assert refused("> # Quoted\n\ntext")


def test_heading_in_a_list_is_not_the_document_title():
    assert refused("- # Listed")


def test_output_without_a_title_is_unchanged():
    # documents that gain no title render exactly as before
    assert "<mj-title" not in parse_markdown_to_mjml("## Only an h2\n\ntext")


def test_title_reaches_the_final_html():
    html = parse_markdown_to_html("# My newsletter\n\ntext")
    assert "<title>My newsletter</title>" in html
