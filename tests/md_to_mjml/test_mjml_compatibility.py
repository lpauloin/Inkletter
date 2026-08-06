"""MJML component-compatibility invariants.

An MJML component emitted inside a raw-HTML context (mj-text, mj-table,
mj-button content) leaks as an unknown tag into the final HTML. These
property tests run a corpus of tricky markdown through the pipeline and
assert it never happens. The corpus grows with every feature; the
checks never change.
"""

import re

import pytest

from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.theme import Theme

CORPUS = [
    # images caught in inline formatting (the fixed leak)
    "**[![alt](https://x.com/i.png)](https://x.com)**",
    "**![gras](https://x.com/i.png)**",
    "*![emphase](https://x.com/i.png)*",
    "~~![barre](https://x.com/i.png)~~",
    "Avant **![i](https://x.com/i.png)** après",
    # images in every mj-text context
    "# Titre ![i](https://x.com/i.png)",
    "# [![i](https://x.com/i.png)](https://x.com)",
    "> citation ![i](https://x.com/i.png)",
    "> [![i](https://x.com/i.png)](https://x.com) citée",
    "- item ![i](https://x.com/i.png)",
    "- [![i](https://x.com/i.png)](https://x.com)",
    "1. ![i](https://x.com/i.png) numéroté",
    "- [ ] tâche ![i](https://x.com/i.png)",
    # images in tables
    "| A |\n|---|\n| ![i](https://x.com/i.png) |",
    "| A |\n|---|\n| [![i](https://x.com/i.png)](https://x.com) |",
    # buttons
    "**[Get started](https://x.com/go)**",
    "**[*Vite* `go` <span>!</span>](https://x.com/go)**",
    "- **[Go](https://x.com/go)**",
    "| A |\n|---|\n| **[Go](https://x.com/go)** |",
    "> **[Go](https://x.com/go)**",
    "# **[Go](https://x.com/go)**",
    # layout conventions
    "![a](https://x.com/a.png) ![b](https://x.com/b.png)",
    "[![a](https://x.com/a.png)](https://x.com) ![b](https://x.com/b.png)",
    "![J](https://x.com/j.png) Un média-objet avec du texte.",
    "Un média-objet inversé. ![J](https://x.com/j.png)",
    # the rest of the syntax, mixed
    "Du `code` et **du gras** et un [lien](https://x.com/?a=1&b=2).",
    "```python\nprint('x')\n```",
    "<div>bloc html</div>\n\nUn <span>inline</span> html.",
    "---",
    # a full document mixing everything
    (
        "# Titre ![i](https://x.com/i.png)\n\n"
        "**[![c](https://x.com/c.png)](https://x.com)**\n\n"
        "![a](https://x.com/a.png) ![b](https://x.com/b.png)\n\n"
        "![J](https://x.com/j.png) Média-objet.\n\n"
        "- [![l](https://x.com/l.png)](https://x.com) item\n\n"
        "| T |\n|---|\n| ![t](https://x.com/t.png) |\n\n"
        "> quote ![q](https://x.com/q.png)\n\n"
        "**[Get started](https://x.com/go)**"
    ),
]

RAW_CONTEXTS = ("mj-text", "mj-table", "mj-button")


def assert_no_component_leak(mjml):
    body = mjml[mjml.find("<mj-body") :]
    for tag in RAW_CONTEXTS:
        for m in re.finditer(rf"<{tag}[^>]*>(.*?)</{tag}>", body, re.S):
            assert "<mj-" not in m.group(
                1
            ), f"MJML component inside {tag}: {m.group(1)!r}"


@pytest.mark.parametrize("markdown", CORPUS)
def test_no_mjml_component_inside_raw_contexts(markdown):
    # D1: no mj-* tag inside mj-text / mj-table / mj-button content
    assert_no_component_leak(parse_markdown_to_mjml(markdown))
    assert_no_component_leak(parse_markdown_to_mjml(markdown, theme=Theme()))


@pytest.mark.parametrize("markdown", CORPUS)
def test_no_mjml_tag_survives_in_final_html(markdown):
    # D2/D3: mjml2html accepts the document and no mj- tag leaks through
    for theme in (None, Theme()):
        html = parse_markdown_to_html(markdown, theme=theme)
        assert "<mj-" not in html


@pytest.mark.parametrize("markdown", CORPUS)
def test_no_leak_with_url_factory(markdown):
    # rewriting URLs must never change the component structure
    from inkletter.shortener import URLFactory

    class Prefix(URLFactory):
        def rewrite_link(self, url):
            return f"https://short.test/?u={url}"

    assert_no_component_leak(parse_markdown_to_mjml(markdown, url_factory=Prefix()))


@pytest.mark.parametrize("markdown", CORPUS)
def test_text_output_is_clean(markdown):
    # the plain-text sibling renders the whole corpus without exception,
    # and never leaks MJML components or HTML tags
    from inkletter.md_to_text import parse_markdown_to_text

    text = parse_markdown_to_text(markdown)
    assert "<mj-" not in text
    assert "<strong>" not in text and "<a href" not in text


# --- Django tags ---


def with_tags(markdown):
    """The same document, wrapped in flow control and given a variable."""
    return (
        f"{{% if show %}}\n\n{markdown}\n\nSigned, {{{{ user.name }}}}\n\n{{% endif %}}"
    )


@pytest.mark.parametrize("markdown", CORPUS)
def test_corpus_is_identical_with_django_tags_on(markdown):
    # the corpus holds no tag, so turning the plugin on must change
    # strictly nothing: opting in is never a behaviour change
    assert parse_markdown_to_mjml(markdown, django_tags=True) == parse_markdown_to_mjml(
        markdown
    )


@pytest.mark.parametrize("markdown", CORPUS)
def test_tagged_corpus_has_no_leak(markdown):
    mjml = parse_markdown_to_mjml(with_tags(markdown), django_tags=True)
    assert_no_component_leak(mjml)
    assert "inktag" not in mjml
    assert "{% if show %}" in mjml and "{{ user.name }}" in mjml


@pytest.mark.parametrize("markdown", CORPUS)
def test_tagged_corpus_compiles_to_html(markdown):
    html = parse_markdown_to_html(with_tags(markdown), django_tags=True)
    assert "<mj-" not in html
    assert "inktag" not in html
    assert "{% if show %}" in html and "{{ user.name }}" in html
