"""An address written in the text without brackets — in full or as a domain
— read as a link to itself."""

import re

from markdown_it.token import Token

from inkletter.plugins.bare_domains import ASSUMED_SCHEME, BARE_DOMAIN

# An address written without brackets, which CommonMark reads as text and
# every reader as a link: read as one, so the URL factory shortens it and
# the counter charges it like any other. It never ends on `*`, `_` or `~`
# (GFM's autolink rule), or `**https://exemple.fr**` would swallow its
# closing marks. A final `)` is matched, and weighed below.
BARE_URL = re.compile(r"""https?:\/\/[^\s<]+[^<.,:;"'\]\s*_~]""")

# What a token leaves just before the text that follows it, for a rule that
# needs to see what an address is written against: a mark's own spelling,
# and these for the tokens that have none.
SPELLED_ENDS = {
    "link_close": ")",
    "image": ")",
    "code_inline": "`",
    "softbreak": "\n",
    "hardbreak": "\n",
    "hashtag": "#",
}


def without_a_sentence_parenthesis(text):
    """GFM's parenthesis rule: a closing parenthesis at the end belongs to
    the address only when an opening one inside it is waiting for it —
    `(see http://a.fr/b)` keeps its sentence's parenthesis,
    `http://a.fr/b_(c)` keeps its own."""
    while text.endswith(")") and text.count(")") > text.count("("):
        text = text[:-1]
    return text


# A hand-written anchor, opening or closing: what it holds is its label.
ANCHOR_OPENS = re.compile(r"<a[\s>]", re.I)
ANCHOR_CLOSES = re.compile(r"</a\s*>", re.I)


def link_depth(token):
    """How far a token takes the text into a link's label, or out of it."""
    if token.type == "html_inline" and ANCHOR_OPENS.match(token.content):
        return 1
    if token.type == "html_inline" and ANCHOR_CLOSES.match(token.content):
        return -1
    return {"link_open": 1, "link_close": -1}.get(token.type, 0)


def is_text(token):
    """Text as the author meant it: written, or an entity spelling a
    character. An escaped character is not: `exemple\\.com` was written
    not to be an address."""
    return token.type == "text" or (token.type == "text_special" and token.info == "entity")


def runs(tokens):
    """The tokens with each run of text joined into one."""
    joined = []
    for token in tokens:
        if is_text(token) and joined and is_text(joined[-1]):
            joined[-1] = Token("text", "", 0, content=joined[-1].content + token.content)
        elif is_text(token):
            joined.append(Token("text", "", 0, content=token.content))
        else:
            joined.append(token)
    return joined


def spelled_before(tokens, index):
    """The character the source holds just before `tokens[index]` — what a
    lookbehind on an address needs once the text is cut into tokens."""
    if index == 0:
        return ""
    previous = tokens[index - 1]
    if previous.type in ("text", "html_inline"):
        return previous.content[-1:]
    if previous.type == "text_special":
        return previous.markup[-1:]
    if previous.type in SPELLED_ENDS:
        return SPELLED_ENDS[previous.type]
    return previous.markup[-1:]


def next_address(text, position):
    """The first bare address of `text` at or after `position`: its start,
    the text written and the URL it leads to; None when there is none. A
    full address wins a tie with a domain inside it."""
    found = [
        (match.start(), rank, match.group(0), scheme)
        for rank, (pattern, scheme) in enumerate(((BARE_URL, ""), (BARE_DOMAIN, ASSUMED_SCHEME)))
        if (match := pattern.search(text, position))
    ]
    if not found:
        return None
    start, _, written, scheme = min(found)
    written = without_a_sentence_parenthesis(written)
    return start, written, scheme + written


def linked(token, before, md):
    """A text token cut at its bare addresses: the text between them, and
    each address as a link labelled with what was written."""
    text = before + token.content
    position, cut = len(before), []
    while address := next_address(text, position):
        start, written, url = address
        if start > position:
            cut.append(Token("text", "", 0, content=text[position:start]))
        opening = Token("link_open", "a", 1, attrs={"href": md.normalizeLink(url)})
        cut += [opening, Token("text", "", 0, content=written), Token("link_close", "a", -1)]
        position = start + len(written)
    if not cut:
        return [token]
    if position < len(text):
        cut.append(Token("text", "", 0, content=text[position:]))
    return cut


def bare_links(state):
    """Reads the bare addresses of every run of text — but inside a link's
    label, written in Markdown or by hand, which holds no link."""
    for block in state.tokens:
        if block.type != "inline":
            continue
        tokens = runs(block.children)
        children, depth = [], 0
        for index, token in enumerate(tokens):
            depth += link_depth(token)
            if token.type == "text" and depth == 0:
                children += linked(token, spelled_before(tokens, index), state.md)
            else:
                children.append(token)
        block.children = children


def bare_links_plugin(md):
    # before the escapes join the text around them: an escaped character
    # is not part of an address
    md.core.ruler.before("text_join", "bare_links", bare_links)
