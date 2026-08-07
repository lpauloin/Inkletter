"""Making a value literal once it lands in a Markdown document.

Only needed when the document is templated and resolved *before* being
converted — the order sample/DJANGO.md documents. There, a value goes
into a **Markdown** document, and Markdown makes links: a value of
`[Click here](https://evil.tld)` becomes a working, clickable link in
the mail you send, and well-formed HTML passes through verbatim.
Escaping for HTML, which is what a template engine does by default,
stops neither.

Nothing in the standard library does this, and neither does mistune —
its `escape` and `safe_entity` are HTML escaping. What *is* standard is
the rule this implements: CommonMark says any ASCII punctuation
character may be backslash-escaped.

For the other place a value can land, a code block, the standard library
already has the answer and this module deliberately does not wrap it:

    import textwrap
    textwrap.indent(response, "    ")

Four spaces make an *indented* code block, and that is the point. A
fenced block is closed by a delimiter, so a value containing ``` ends it
early and everything after is parsed as Markdown. An indented block has
no delimiter to escape. `textwrap.indent` even leaves blank lines
alone, which is exactly what the spec wants inside one.
"""

import re

#: Every ASCII punctuation character, which CommonMark allows to be
#: backslash-escaped. Escaping the lot is blunt on purpose: guessing
#: which ones are dangerous in which position is how you miss one. The
#: backslashes are markup, so they disappear when the Markdown is
#: parsed and no reader ever sees them.
PUNCTUATION = re.compile(r"([!-/:-@\[-`{-~])")


def escape_markdown(value):
    """Return `value` so that Markdown reads it as plain text.

    Use it on everything that is not yours — a name, a filename, a
    label from an API. Your own words, the ones you wrote in the
    template, need nothing.
    """
    return PUNCTUATION.sub(r"\\\1", str(value))
