"""Everything Inkletter raises on purpose.

All three are failures of the *input*, not of the conversion, and none is
recoverable: the doctrine is the loud failure, since a half-rendered
email is worse than none. Their messages are written for the author —
what is wrong, and what to write instead.
"""


class ThemeError(Exception):
    """Invalid theme definition (unknown key, bad type, unknown preset)."""


class MarkupError(Exception):
    """The Markdown says something Inkletter cannot honour.

    Raised for an image attribute block: an unknown key, a length in a
    unit email cannot rely on, an alignment that is not one.
    """


class LengthError(Exception):
    """The rendered text is longer than the destination accepts.

    Raised rather than truncated: a post cut mid-sentence without warning
    is worse than one that refuses to leave. Carries what was measured and
    what was allowed, so a caller can say by how much.
    """

    def __init__(self, length, limit, what="post"):
        self.length, self.limit, self.what = length, limit, what
        super().__init__(
            f"the {what} is {length} characters long, {limit} allowed ({length - limit} over)"
        )
