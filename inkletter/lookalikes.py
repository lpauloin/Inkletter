"""Unicode look-alikes of bold, italic and strikethrough — for a text that
has no formatting of its own: a plain-text destination, a document pasted
into an editor that keeps no strike.

They are text, not formatting: a screen reader spells them out letter by
letter and a search does not match them, which is why every output asks
for them rather than having them by default.

| Styles in force  | Letters become                                        |
|------------------|-------------------------------------------------------|
| bold             | 𝗺𝗼𝘁 𝟮𝟬𝟮𝟲 sans-serif bold, digits too                    |
| italic           | 𝘮𝘰𝘵 sans-serif italic — Unicode has no italic digit    |
| bold and italic  | 𝙢𝙤𝙩 𝟮𝟬𝟮𝟲 sans-serif bold italic, the bold digits — one  |
|                  | table, whichever is outside: a second table would     |
|                  | find no ASCII letter left to map                      |
| strikethrough    | a combining stroke after each letter, digit, sign or  |
|                  | space — never an emoji — and after the accents that   |
|                  | follow it, on top of the letters' own look-alike      |

**An accented letter** has no look-alike of its own: it goes out as the
look-alike of its letter followed by its accents (`𝗲` + U+0301 for `é`),
which reads as one bold or italic letter. Measured on LinkedIn on
2026-11-10: a lower-case letter carries any accent, and a capital an accent
under it (`Ç`); **a capital with an accent above it** (`É`, `À`, `Ê`) loses
it under the look-alike's own height, so it stays as it is — plain, but
spelt right. A letter whose base is not ASCII (`œ`, `ß`) stays as it is.
"""

import unicodedata
from collections.abc import Collection
from string import ascii_letters, ascii_uppercase, digits


def lookalikes(lower, upper, figures=None):
    targets = [*range(lower, lower + 26), *range(upper, upper + 26)]
    sources = ascii_letters
    if figures is not None:
        targets += range(figures, figures + 10)
        sources += digits
    return str.maketrans(sources, "".join(map(chr, targets)))


# The sans-serif bold digits; there are no italic ones.
BOLD_DIGITS = 0x1D7EC
LETTERS = {
    frozenset({"bold"}): lookalikes(0x1D5EE, 0x1D5D4, BOLD_DIGITS),
    frozenset({"italic"}): lookalikes(0x1D622, 0x1D608),
    frozenset({"bold", "italic"}): lookalikes(0x1D656, 0x1D63C, BOLD_DIGITS),
}
# The combining marks drawn above a letter — grave to the comma above,
# the horn and the left angle above: lost on a capital's look-alike.
ABOVE = (range(0x0300, 0x0316), range(0x031A, 0x031C))


def is_above(mark):
    return any(ord(mark) in marks for marks in ABOVE)


def decomposed(char):
    """An accented letter as its ASCII letter and its accents, when its
    look-alike keeps them; the letter itself otherwise."""
    parts = unicodedata.normalize("NFD", char)
    letter, marks = parts[0], parts[1:]
    if not marks or letter not in ascii_letters:
        return char
    if letter in ascii_uppercase and any(map(is_above, marks)):
        return char
    return parts


STRIKE = "\u0336"
# What the stroke goes after: letters, digits, punctuation, spaces and the
# like. Not an emoji, nor what an emoji is built of — a joiner, a variation
# selector, a skin tone — where a stroke breaks the picture instead of
# crossing it out.
STRUCK_CATEGORIES = ("L", "N", "P", "Zs", "Sc", "Sm")
# What belongs to the character before it — an accent, a vowel sign: the
# stroke goes after them, or it would sit between a letter and its accent.
COMBINING_CATEGORIES = ("Mn", "Mc")


def is_struck(char):
    return unicodedata.category(char).startswith(STRUCK_CATEGORIES)


def clusters(text):
    """Each character with the combining marks that follow it."""
    found = []
    for char in text:
        if found and unicodedata.category(char) in COMBINING_CATEGORIES:
            found[-1] += char
        else:
            found.append(char)
    return found


def strike(text: str, before: str = "", after: str = "") -> str:
    """A stroke after each character it goes after, past its combining
    marks — and **not on a space that touches something it skips**: an
    emoji is left whole, but a stroke on the space beside it runs into the
    picture all the same, which is the very thing skipping it avoids.

    `before` and `after` are the struck text around this one, written
    apart — another style, another tag —: read for the neighbours of a
    space at an edge, never struck here."""
    own = clusters(text)
    edge_before = clusters(before)[-1:]
    line = edge_before + own + clusters(after)[:1]
    marked = []
    for at, cluster in enumerate(own, start=len(edge_before)):
        base = cluster[0]
        struck = is_struck(base)
        if struck and unicodedata.category(base) == "Zs":
            neighbours = [line[i][0] for i in (at - 1, at + 1) if 0 <= i < len(line)]
            struck = all(map(is_struck, neighbours))
        marked.append(cluster + STRIKE if struck else cluster)
    return "".join(marked)


def substitute(text: str, styles: Collection[str]) -> str:
    """`text` in the look-alikes of `styles`."""
    letters = LETTERS.get(frozenset(styles) & {"bold", "italic"})
    if letters:
        text = "".join(map(decomposed, text)).translate(letters)
    if "strikethrough" in styles:
        text = strike(text)
    return text
