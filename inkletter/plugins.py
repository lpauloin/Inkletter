"""What Inkletter teaches mistune to read, beyond CommonMark.

Each plugin registers one inline rule; `parse_markdown_to_ast` decides
which ones a document gets. The attribute block (`{width=…}`) is one too,
and keeps its own module: it carries a grammar of its own.
"""

from mistune.util import escape_url

# A hashtag, read before the marks inside it: `#équipe_rh` is one tag, where
# the emphasis rule would have seen an `_` to open an italic. Not a heading:
# a heading is a block, decided line by line before any inline rule runs,
# and it needs a space after its `#`. Not after a word character, `&` (an
# entity) or another `#` either.
HASHTAG_PATTERN = r"(?<![\w&#])#(?=\w*[^\W\d_])\w+"


def parse_hashtag(inline, m, state):
    state.append_token({"type": "hashtag", "attrs": {"name": m.group(0)[1:]}})
    return m.end()


def hashtag_plugin(md):
    md.inline.register("hashtag", HASHTAG_PATTERN, parse_hashtag)


# mistune's bare-address rule, less its one defect: an address never ends on
# `*`, `_` or `~` (GFM's autolink rule), or `**https://exemple.fr**` swallows
# its closing marks — the address becomes `https://exemple.fr**`, and the bold
# around it is never read. A final `)` is matched, and weighed by the parser.
BARE_URL_PATTERN = r"""https?:\/\/[^\s<]+[^<.,:;"'\]\s*_~]"""


def parse_bare_url(inline, m, state):
    """mistune's own reading of the match, with GFM's parenthesis rule:
    a closing parenthesis at the end belongs to the address only when an
    opening one inside it is waiting for it — `(see http://a.fr/b)` keeps
    its sentence's parenthesis, `http://a.fr/b_(c)` keeps its own."""
    text = m.group(0)
    while text.endswith(")") and text.count(")") > text.count("("):
        text = text[:-1]
    if state.in_link:
        inline.process_text(text, state)
    else:
        state.append_token(
            {
                "type": "link",
                "children": [{"type": "text", "raw": text}],
                "attrs": {"url": escape_url(text)},
            }
        )
    return m.start() + len(text)


def bare_url_plugin(md):
    md.inline.register("url_link", BARE_URL_PATTERN, parse_bare_url)
