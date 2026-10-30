"""An address written in the text without brackets — in full or as a domain
— read as a link to itself.

| Written                | Rule                                                 |
|------------------------|------------------------------------------------------|
| `https://exemple.fr/…` | inline, at its `:` — read whole before any mark, so  |
|                        | `https://a.fr/*x*` keeps its stars (markdown-it's    |
|                        | own linkify rule works the same way)                 |
| `exemple.fr/…`         | core, in the text once its marks are read: nothing   |
|                        | announces a domain to an inline rule                 |
"""

import re

from markdown_it.common.utils import unescapeAll
from markdown_it.token import Token

from inkletter.plugins.bare_domains import ASSUMED_SCHEME, BARE_DOMAIN

# An address written without brackets, which CommonMark reads as text and
# every reader as a link: read as one, so the URL factory shortens it and
# the counter charges it like any other. Where it starts and ends is
# LinkedIn's, measured in its own composer:
#
# | Around the address                 | Read                                 |
# |------------------------------------|--------------------------------------|
# | after a space, the start, `(`, `"` | an address — and after a mark        |
# |                                    | (`*`, `_`, `~`), which the post      |
# |                                    | drops (GFM's own rule)               |
# | after a letter, `«`, `“`, `'`, `-` | text: `xhttps://…`, `«https://…»`    |
# | ending on `.`, `,`, `:`, `;`, `"`, | the sign is the sentence's, not the  |
# | `'`, `?`, `!`, `]`, `*`, `_`, `~`  | address's — nor `**`'s around it     |
#
# A final `)` is matched, and weighed below.
BARE_URL = re.compile(r"""(?<![^\s(*_~"])https?:\/\/[^\s<]+[^<.,:;"'\]\s*_~?!]""")
# The scheme the text before a `:` ends on.
SCHEME = re.compile(r"https?$")


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
    """The character the source holds just before `tokens[index]`, when the
    domain's lookbehind needs it: the end of a text, or an escaped
    character (`\\.exemple.com` is no domain). Every other token ends on a
    sign the lookbehind lets by."""
    if index == 0:
        return ""
    previous = tokens[index - 1]
    if previous.type in ("text", "html_inline"):
        return previous.content[-1:]
    if previous.type == "text_special":
        return previous.markup[-1:]
    return ""


# --- In full: inline, at its `:` ---


def bare_url(state, silent):
    """An address in full, read when the text reaches its `:` — its scheme
    already written, waiting to be taken back."""
    if state.linkLevel > 0 or not state.src.startswith("://", state.pos):
        return False
    scheme = SCHEME.search(state.pending)
    if scheme is None:
        return False
    start = state.pos - len(scheme.group(0))
    match = BARE_URL.match(state.src, start)
    if match is None:
        return False
    written = without_a_sentence_parenthesis(match.group(0))
    if not silent:
        state.pending = state.pending[: -len(scheme.group(0))]
        # its entities read, like the text around it
        url = unescapeAll(written)
        state.push("link_open", "a", 1).attrs = {"href": state.md.normalizeLink(url)}
        state.push("text", "", 0).content = url
        state.push("link_close", "a", -1)
    state.pos = start + len(written)
    return True


# --- As a domain: in the text, once its marks are read ---


def next_address(text, position):
    """The first domain of `text` at or after `position`: its start, the
    text written and the URL it leads to; None when there is none."""
    match = BARE_DOMAIN.search(text, position)
    if match is None:
        return None
    written = without_a_sentence_parenthesis(match.group(0))
    return match.start(), written, ASSUMED_SCHEME + written


def linked(md, token, before):
    """A text token cut at its domains: the text between them, and each
    domain as a link labelled with what was written."""
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


def bare_domains(state):
    """Reads the domains of every run of text — but inside a link's label,
    written in Markdown or by hand, which holds no link."""
    for block in state.tokens:
        if block.type != "inline":
            continue
        tokens = runs(block.children)
        children, depth = [], 0
        for index, token in enumerate(tokens):
            depth += link_depth(token)
            if token.type == "text" and depth == 0:
                children += linked(state.md, token, spelled_before(tokens, index))
            else:
                children.append(token)
        block.children = children


def bare_links_plugin(md):
    md.inline.ruler.before("linkify", "bare_url", bare_url)
    # before the escapes join the text around them: an escaped character
    # is not part of an address
    md.core.ruler.before("text_join", "bare_domains", bare_domains)
