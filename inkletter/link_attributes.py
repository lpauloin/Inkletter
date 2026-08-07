"""Pandoc's `link_attributes`, narrowed to what an email can honour.

    ![Acme](logo@2x.png){width=96px align=left}

A logo exported at 2x arrives twice too large unless the document says
how wide to draw it, and no theme can say it: the theme does not know
which image you inserted. A dimension is a fact about the asset; an
appearance is a choice of theme. That line is why width, height and
align are accepted here and no CSS property ever will be.

The block decorates the token it is glued to — an image, or a link
holding one. Anything else gives the hand back and the braces stay
literal text, which is also the author's escape hatch: a single space
before the brace is enough.
"""

import re

from inkletter.exceptions import MarkupError

#: The only keys. Unlike Pandoc, an unknown one raises instead of
#: becoming a data-* attribute: a typo in an email cannot be taken back
#: once it is sent.
KEYS = ("width", "height", "align")

#: mj-image knows these three. Pandoc and mistune also accept
#: top/middle/bottom, which are vertical-align and have no equivalent.
ALIGNMENTS = ("left", "center", "right")

#: px and % only. Pandoc also takes cm/mm/in — physical units mean
#: nothing on a screen — and mistune takes em/rem/vw/vh, unreliable in
#: Outlook. A bare number means px, as in Pandoc.
DIMENSION = re.compile(r"(\d+(?:\.\d+)?)(px|%)?$")

#: A brace block on one line. Matched loosely on purpose: what is
#: inside decides whether it is an attribute block at all.
BLOCK_PATTERN = r"\{(?P<ink_body>[^{}\n]*)\}"

#: One token: key=value, the value optionally quoted. The group names
#: are free here — only the pattern registered with mistune shares its
#: namespace with the rule name.
TOKEN = re.compile(r'(?P<key>[A-Za-z][\w-]*)=(?P<value>"[^"]*"|\'[^\']*\'|[^\s"\'{}]+)')


def parse_pairs(body):
    """The key/value pairs of a brace block, or None if it is not one.

    Strict by design: one malformed token and the whole block stops
    being an attribute block. That is what lets `{beta}` or
    `{see below}` travel through as ordinary text without anyone having
    to recognise them.
    """
    pairs = []
    position = 0
    for match in TOKEN.finditer(body):
        if body[position : match.start()].strip():
            return None  # stray text between two tokens
        position = match.end()
        pairs.append((match.group("key"), match.group("value").strip("\"'")))
    if body[position:].strip() or not pairs:
        return None
    return pairs


def check_dimension(key, value):
    """A width or a height, normalised — a bare number means px."""
    match = DIMENSION.fullmatch(value)
    if not match:
        raise MarkupError(f"'{key}={value}' is not a length; emails can rely on px and % only")
    number, unit = match.groups()
    return f"{number}{unit or 'px'}"


def check_align(value):
    if value not in ALIGNMENTS:
        raise MarkupError(f"'align={value}' is not an alignment; use left, center or right")
    return value


def build(pairs):
    """The validated attributes of a block. Raises on anything else."""
    attributes = {}
    for key, value in pairs:
        if key not in KEYS:
            raise MarkupError(
                f"unknown image attribute '{key}'; the theme decides how images "
                f"look. Attributes carry facts about the asset: "
                f"{', '.join(KEYS)}."
            )
        if key in attributes:
            raise MarkupError(f"'{key}' is set twice")
        attributes[key] = check_align(value) if key == "align" else check_dimension(key, value)
    return attributes


def carries_an_image(token):
    """An image, or a link holding one — the two shapes that can be sized."""
    if token is None:
        return False
    if token["type"] == "image":
        return True
    return token["type"] == "link" and any(
        child["type"] == "image" for child in token.get("children", [])
    )


def parse_attrs(inline, m, state):
    previous = state.tokens[-1] if state.tokens else None
    if not carries_an_image(previous):
        return None  # give the hand back: the braces stay literal
    pairs = parse_pairs(m.group("ink_body"))
    if pairs is None:
        return None
    previous.setdefault("attrs", {})["ink_attributes"] = build(pairs)
    return m.end()


def link_attributes(md):
    """The plugin, passed to mistune.create_markdown(plugins=[...])."""
    # before "escape" so the block wins over an escaped brace; a code
    # span still wins over it, its match starting earlier
    md.inline.register("ink_attrs", BLOCK_PATTERN, parse_attrs, before="escape")
