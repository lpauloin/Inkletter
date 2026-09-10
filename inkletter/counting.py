"""What a LinkedIn post costs, in the unit the platform counts.

Three units compete for the word "character": a Unicode code point, a
UTF-16 code unit, and a grapheme. An emoji is one, two and one of them
respectively, so a counter that picks the wrong one lets through a post the
platform will refuse.

Measured against the platform's own refusal, which reports the length it
computed: it counts **UTF-16 code units**. A plain emoji costs 2, a skin
tone or a flag 4, a joined family 8, a letter in a Unicode bold substitute
2. Whitespace and line breaks count; a trailing one does not, being trimmed
before it is read.

**The count is accumulated as the document is rendered, never taken over
the finished string**, because only the rendering knows what each fragment
is. A mention weighs the name it displays rather than the marker carrying
it, and a link weighs the short link it will become — a width that does not
exist yet. Once the string is produced, a mention's marker is text like any
other, which a code block could have contained word for word.

This module therefore holds the unit, the platform's own ceiling, and what
each kind of fragment costs — one function per kind, called at the moment
that fragment is written. Rules, and nothing that walks a document: the
summing belongs to whoever renders one.
"""

# What the platform accepts, measured: beyond this it refuses the text
# outright. Every other ceiling belongs to the caller and comes in as
# `max_length`.
MAX_LENGTH = 4000


def utf16_length(text):
    """The unit LinkedIn counts in."""
    return len(text.encode("utf-16-le")) // 2


# --- What each kind of fragment costs ---
#
# One function per kind, because two of them are not their own characters
# and the rule for each is a fact about the platform rather than about the
# string: measured, a mention weighs the name it displays, and an address
# on its way to a shortener will weigh whatever that shortener produces.


def cost_of_text(text):
    """Ordinary text: what it says."""
    return utf16_length(text)


def cost_of_mention(name):
    """A mention: the name the platform displays, never the marker that
    carries it — measured, 10 for a marker of 43."""
    return utf16_length(name)


def cost_of_link(url, link_length=None):
    """A link: the width of the short link it will become, when whoever
    shortens says what that width is; the address as written otherwise."""
    return utf16_length(url) if link_length is None else link_length
