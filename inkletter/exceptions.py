"""Everything Inkletter raises on purpose.

A failure of the *input*, not of the conversion, and not recoverable:
the doctrine is the loud failure, since a half-rendered email is worse
than none. The message is written for the author of the theme — what is
wrong, and what to change.
"""


class ThemeError(Exception):
    """Invalid theme definition (unknown key, bad type, unknown preset)."""
