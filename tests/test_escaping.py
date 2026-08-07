"""Making a value literal in a Markdown document, and why it matters.

These are security controls: without escaping, a value coming from a
user or a third party *is* Markdown, and Markdown makes links. Each
test states the attack it closes and sits next to a control case, so
none of them can quietly stop measuring anything.

No Django here, and none needed — the escaping is a plain function and
the code-block half is `textwrap.indent`.
"""

import html as html_module
import textwrap

import pytest

from inkletter import escape_markdown
from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_text import parse_markdown_to_text


def email(markdown):
    return parse_markdown_to_html(markdown), parse_markdown_to_text(markdown)


# --- A value in the flow of the text ---


@pytest.mark.parametrize(
    "value",
    [
        "_Bob_",
        "**shouting**",
        "# not a heading",
        "- not a list item",
        "Invoices | Q3",
        "back\\slash",
        "1. not an ordered list",
        "> not a quote",
    ],
)
def test_an_escaped_value_stays_literal(value):
    html, text = email(f"Value: {escape_markdown(value)}.")
    print(html)
    print(text)
    assert value in text
    # the HTML half escapes for HTML on top, as it must
    assert html_module.escape(value, quote=False) in html


def test_escaping_stops_a_link_from_being_planted():
    # the attack: a value that becomes a working link in the mail you
    # send, pointing wherever its author chose
    hostile = "[Click here](https://evil.tld)"
    html, text = email(f"Value: {escape_markdown(hostile)}.")
    print(html)
    assert 'href="https://evil.tld"' not in html
    assert hostile in html
    assert hostile in text


def test_without_escaping_that_link_is_clickable():
    # the control case, so the test above is not measuring nothing
    html, _ = email("Value: [Click here](https://evil.tld).")
    print(html)
    assert 'href="https://evil.tld"' in html


def test_escaping_stops_html_from_passing_through():
    html, _ = email(f"Value: {escape_markdown('<script>alert(1)</script>')}.")
    print(html)
    assert "<script>" not in html
    assert "alert(1)" in html


def test_the_backslashes_never_reach_the_reader():
    # they are markup, and markup disappears when the Markdown is parsed
    _, text = email(f"Sent by {escape_markdown('Ben & Jerry')}.")
    print(text)
    assert text.strip() == "Sent by Ben & Jerry."
    assert "\\" not in text


def test_it_accepts_what_is_not_a_string():
    assert escape_markdown(42) == "42"


# --- A value as a code block ---
#
# The standard library does this one: textwrap.indent with four spaces.
# These tests are here because the *choice* needs defending, not the
# implementation.


SERVER_RESPONSE = "erreur: champ manquant"

#: A value that ends the fenced block it was put in, and writes its own
#: Markdown after it.
FENCE_BREAKER = "ok\n```\n\n**INJECTED** and [a link](https://evil.tld)\n\n```"


def as_code_block(value):
    return textwrap.indent(str(value), "    ")


def test_an_indented_block_survives_a_value_that_closes_a_fence():
    # the attack: a fenced block is closed by a delimiter, and a value
    # containing one escapes it. An indented block has no delimiter.
    html, _ = email(f"Server said:\n\n{as_code_block(FENCE_BREAKER)}\n")
    print(html)
    assert "<strong>INJECTED</strong>" not in html
    assert 'href="https://evil.tld"' not in html
    assert "INJECTED" in html  # still shown, as the text it is


def test_a_fence_really_is_escapable():
    # the control case: the same value in a fence does break out
    html, _ = email(f"Server said:\n\n```\n{FENCE_BREAKER}\n```\n")
    print(html)
    assert "<strong>INJECTED</strong>" in html
    assert 'href="https://evil.tld"' in html


def test_escaping_is_unusable_inside_a_code_block():
    # why the two halves need different treatment: in a code block the
    # backslashes are content, not markup, and the reader sees them
    _, text = email(f"Server said:\n\n{as_code_block(escape_markdown(SERVER_RESPONSE))}\n")
    print(text)
    assert "erreur\\: champ manquant" in text


def test_an_indented_block_reads_cleanly():
    _, text = email(f"Server said:\n\n{as_code_block(SERVER_RESPONSE)}\n")
    print(text)
    assert SERVER_RESPONSE in text
    assert "\\" not in text


def test_blank_lines_stay_blank_inside_the_block():
    # textwrap.indent leaves them alone, which is what the spec wants:
    # a blank line does not end an indented block
    block = as_code_block("first\n\nsecond")
    print(repr(block))
    assert block == "    first\n\n    second"
    html, _ = email(f"Server said:\n\n{block}\n")
    assert "first" in html and "second" in html
    assert html.count("<pre") == 1
