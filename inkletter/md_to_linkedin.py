"""The LinkedIn output: a Markdown document rendered as a post.

A third target beside the MJML/HTML mail and the plain-text alternative,
and the closest to that last one — the platform has no rich formatting, so
a post is text. What this adds is everything a feed does differently: what
a link looks like, what a mention is made of, and how long the whole thing
is in the unit the platform counts.

**One document in, one text out.** A first comment is a second document,
rendered by a second call with its own ceiling: it is written apart, it is
published apart, and it is counted apart.

It never publishes, never looks a mention up, and never truncates: a post
over the ceiling raises rather than leaving cut mid-sentence.
"""

import unicodedata

from inkletter.counting import MAX_LENGTH
from inkletter.exceptions import LengthError
from inkletter.md_to_ast import parse_markdown_to_ast
from inkletter.shortener import URLFactory
from inkletter.visitors.linkedingen import LinkedinCodegen, LinkedinRender


def render_linkedin(
    markdown_text: str,
    unicode_styling: bool = False,
    url_factory: URLFactory | None = None,
) -> LinkedinRender:
    """The post, what the platform counts for it, and what a feed shows of
    it line by line — refused by no ceiling: the caller weighs it."""
    # Composed accents, always: the platform counts a decomposed one as two
    # units and shows it as one, so a text pasted from an editor that writes
    # them decomposed would pay a unit per accented letter for nothing.
    # Canonically equivalent, visually identical, and cheaper.
    markdown_text = unicodedata.normalize("NFC", markdown_text)
    # No button on a feed: a bold link stays a bold link, and reaches the
    # factory as one — `is_bold` — which is how a caller still tells the
    # call to action from a link cited in passing.
    ast = parse_markdown_to_ast(
        markdown_text,
        bold_link_is_button=False,
        url_factory=url_factory,
    )
    return LinkedinCodegen(
        unicode_styling=unicode_styling,
        link_length=None if url_factory is None else url_factory.link_length,
    ).render(ast)


def parse_markdown_to_linkedin(
    markdown_text: str,
    unicode_styling: bool = False,
    url_factory: URLFactory | None = None,
    max_length: int | None = MAX_LENGTH,
) -> str:
    """The post, refused over `max_length` rather than cut."""
    render = render_linkedin(markdown_text, unicode_styling, url_factory)
    if max_length is not None and render.length > max_length:
        raise LengthError(render.length, max_length)
    return render.text
