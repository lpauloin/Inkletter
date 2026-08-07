"""Everything Inkletter raises on purpose.

Both are failures of the *input*, not of the conversion, and neither is
recoverable: the doctrine is the loud failure, since a half-rendered
email is worse than none. Both messages are written for the author —
what is wrong, and what to write instead.
"""


class ThemeError(Exception):
    """Invalid theme definition (unknown key, bad type, unknown preset)."""


class MarkupError(Exception):
    """The Markdown says something Inkletter cannot honour.

    Raised for an image attribute block: an unknown key, a length in a
    unit email cannot rely on, an alignment that is not one.
    """
