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

#: mj-image knows these three. Pandoc also accepts
#: top/middle/bottom, which are vertical-align and have no equivalent.
ALIGNMENTS = ("left", "center", "right")

#: px only. Pandoc also takes cm/mm/in — physical units mean nothing on
#: a screen — and em/rem/vw/vh are unreliable in Outlook. A
#: percentage is refused rather than quietly dropped: mj-image sizes in
#: pixels, so `width=50%` came out at the full column width, which is
#: the shape of error this syntax exists to avoid. A bare number means
#: px, as in Pandoc.
DIMENSION = re.compile(r"(\d+(?:\.\d+)?)(px)?$")

#: A brace block on one line. Matched loosely on purpose: what is
#: inside decides whether it is an attribute block at all.
BLOCK = re.compile(r"\{([^{}\n]*)\}")

#: One token: key=value, the value optionally quoted.
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
        raise MarkupError(f"'{key}={value}' is not a length; mj-image sizes in px only")
    number, unit = match.groups()
    return f"{number}{unit or 'px'}"


def check_align(value):
    if value not in ALIGNMENTS:
        raise MarkupError(f"'align={value}' is not an alignment; use {', '.join(ALIGNMENTS)}")
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


def image_decorated(tokens):
    """The image the block glued to the last token decorates — that token,
    or the image inside the link it closes — or None: anything else gives
    the hand back."""
    if not tokens:
        return None
    last = tokens[-1]
    if last.type == "image":
        return last
    if last.type != "link_close":
        return None
    depth = 0
    for token in reversed(tokens[:-1]):
        if token.type == "link_open" and depth == 0:
            return None
        depth += {"link_close": 1, "link_open": -1}.get(token.type, 0)
        if token.type == "image" and depth == 0:
            return token
    return None


def attribute_block(state, silent):
    if state.src[state.pos] != "{":
        return False
    # glued to the token before it: a space in between is the author's
    # escape hatch, and Pandoc's
    image = None if state.pending else image_decorated(state.tokens)
    match = BLOCK.match(state.src, state.pos)
    if image is None or match is None:
        return False  # give the hand back: the braces stay literal
    pairs = parse_pairs(match.group(1))
    if pairs is None:
        return False
    if not silent:
        attributes = build(pairs)
        # a block written after a link decorates the image it wraps, so
        # both spellings land in the same place — the image's own first
        image.meta.setdefault("ink_attributes", attributes)
    state.pos = match.end()
    return True


def link_attributes_plugin(md):
    """The plugin, passed to `MarkdownIt.use`."""
    md.inline.ruler.before("emphasis", "ink_attrs", attribute_block)
