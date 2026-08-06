"""A mistune plugin making Django template tags first-class AST nodes.

Without it, Markdown and MJML destroy the tags three ways: a spaced
destination is not a link at all, mistune percent-encodes the braces of
the ones that parse, and the codegen HTML-escapes their content. Here
each tag becomes an opaque token instead, so it travels through the
whole pipeline untouched and comes out byte for byte.

The delimiters are the Django Template Language ones, and nothing else.
"""

import re

# Single-line by design: the Django lexer is single-line too.
VARIABLE = r"\{\{(?:(?!\}\}).)*\}\}"
STATEMENT = r"\{%(?:(?!%\}).)*%\}"
COMMENT = r"\{#(?:(?!#\}).)*#\}"

TAG = f"(?:{VARIABLE}|{STATEMENT}|{COMMENT})"

# A tag anywhere in the text. Registered before "escape" so it wins over
# emphasis ({{p*2*x}} stays whole); a code span still wins over it, since
# its match starts earlier.
TAG_PATTERN = TAG

# A link or image whose destination holds a tag — the case CommonMark
# cannot parse (spaces are forbidden there) and that mistune would
# percent-encode. We match the whole construct and build the token
# ourselves, so the destination stays verbatim.
LINK_PATTERN = (
    r"(?P<django_bang>!?)\[(?P<django_label>[^\[\]]*)\]"
    r"\(\s*(?P<django_dest>[^()]*" + TAG + r"[^()]*?)\s*"
    r'(?:"(?P<django_title>[^"]*)")?\s*\)'
)

# <{{ url }}> — the built-in autolink requires a scheme.
AUTOLINK_PATTERN = r"<(?P<django_auto>" + TAG + r")>"

# A line made only of statements (or comments): a block of its own, so
# the flow control can wrap whole elements instead of sitting inside a
# paragraph.
BLOCK_PATTERN = r"^ {0,3}(?:(?:" + STATEMENT + r"|" + COMMENT + r")[ \t]*)+(?:\n|$)"


def parse_tag(inline, m, state):
    state.append_token({"type": "django_tag", "raw": m.group(0)})
    return m.end()


def parse_link(inline, m, state):
    label_state = state.copy()
    label_state.src = m.group("django_label")
    token = {
        "type": "image" if m.group("django_bang") else "link",
        "children": inline.render(label_state),
        "attrs": {"url": m.group("django_dest")},
    }
    if m.group("django_title"):
        token["attrs"]["title"] = m.group("django_title")
    state.append_token(token)
    return m.end()


def parse_autolink(inline, m, state):
    url = m.group("django_auto")
    state.append_token(
        {
            "type": "link",
            "children": [{"type": "text", "raw": url}],
            "attrs": {"url": url},
        }
    )
    return m.end()


def parse_block(block, m, state):
    state.append_token({"type": "django_statement", "raw": m.group(0).strip()})
    return m.end()


def django_tags(md):
    """The plugin, passed to mistune.create_markdown(plugins=[...])."""
    md.block.register(
        "django_statement",
        BLOCK_PATTERN,
        parse_block,
        before="list",
    )
    md.inline.register(
        "django_link",
        LINK_PATTERN,
        parse_link,
        before="link",
    )
    md.inline.register(
        "django_autolink",
        AUTOLINK_PATTERN,
        parse_autolink,
        before="auto_link",
    )
    md.inline.register(
        "django_tag",
        TAG_PATTERN,
        parse_tag,
        before="escape",
    )


#: Matches a tag inside a plain string (a URL, an attribute value) —
#: for the passes that inspect strings rather than nodes.
TAG_RE = re.compile(TAG)


def contains_tag(text):
    return bool(TAG_RE.search(text))


class TagMask:
    """Holds the tags aside while the MJML compiler does its work.

    mjml2html parses its input as XML, so the < of a comparison would
    make it raise, and the codegen escapes attribute values on the way,
    which would turn the quotes of {% url 'name' %} into &#x27;. Each
    tag therefore travels as a plain ASCII token and comes back once
    nothing can mangle it.

    Plain ASCII is not a default, it is the only alphabet that works.
    An invisible character would be collision-proof by nature, but the
    compiler escapes exactly those: U+200B, U+FEFF, U+2060 and the
    private use area all come out of an attribute as the literal text
    \\u{200b}, while control characters are illegal XML and make it
    raise. Accented letters, being printable, do survive — it is the
    invisible ones it rewrites. Do not reach for them again.

    Only the MJML leg needs this. The text output writes its tags out
    as they are.
    """

    # A token reads inktag0x: the prefix finds it again, the number tells
    # one token from the next, and the closing x ends that number —
    # without it, "{{ n }}5 items" would leave inktag05 and the lookup
    # would land on the wrong token.
    PREFIX = "inktag"

    def __init__(self, source=""):
        self.tags = {}  # token -> the tag it stands for
        self.prefix = self.PREFIX
        # never shadow something the author actually wrote
        while self.prefix in source:
            self.prefix += "z"

    def hide(self, text):
        """Swap every tag of a string for a token standing in for it."""

        def take(match):
            token = f"{self.prefix}{len(self.tags)}x"
            self.tags[token] = match.group()
            return token

        return TAG_RE.sub(take, text)

    def reveal(self, text):
        """Put the tags back, byte for byte."""
        if not self.tags:
            return text
        return re.sub(rf"{self.prefix}\d+x", lambda m: self.tags[m.group()], text)
