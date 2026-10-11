"""A domain written without its scheme — `exemple.com`,
`www.exemple.fr/page` — read as a link to `https://` plus what was written:
every feed and every mail reader makes it clickable, so the URL factory is
offered it like an address written in full.

| Written                 | Read as                                      |
|-------------------------|----------------------------------------------|
| `www.exemple.museum`    | a link: `www.` says it, whatever the ending  |
| `exemple.com/a?b=1`     | a link, path and query included              |
| `exemple.co.uk`         | a link: the name ends on a listed extension  |
| `Exemple.com`           | a link: only the extension is lower case     |
| `fini.De retour`        | text: a space forgotten after a full stop    |
| `readme.md`, `node.js`  | text: not an extension of the list           |
| `exemple.community`     | text: the extension must end the name        |
| `exemple.com.zip`       | text: the name goes on past the extension    |
| `a@exemple.com`         | text: a mail address is not a page           |

The list of extensions is closed on purpose. One that is also a common word
or a file's — `me`, `la`, `il`, `sh`, `py`, `md` — would make links out of
sentences; `https://` in front always works for those.
"""

import re

from inkletter.plugins import append_address, without_a_sentence_parenthesis

EXTENSIONS = (
    "com", "net", "org", "info", "biz",
    "io", "co", "ai", "app", "dev", "tech",
    "fr", "eu", "be", "ch", "lu", "ca",
    "uk", "de", "es", "it", "nl", "pt", "us",
)  # fmt: skip

#: The scheme a domain written without one is given.
ASSUMED_SCHEME = "https://"

# One label of a host name: unaccented letters and digits, hyphens inside
# only. An accented name is written with its scheme: its address is not
# the letters typed, and guessing the encoding is not this rule's to do.
LABEL = r"[A-Za-z0-9]+(?:-+[A-Za-z0-9]+)*"
LABELS = rf"(?:{LABEL}\.)+"

# | Part          | What it holds                                           |
# |---------------|---------------------------------------------------------|
# | `NOT_INSIDE`  | not in a word, a mail address, a tag, a path or a       |
# |               | longer name — an `_` is a mark beside the name, not a   |
# |               | letter of it                                            |
# | `WWW_NAME`    | a name opening on `www.`, whatever its ending           |
# | `LISTED_NAME` | a name ending on an extension of the list               |
# | `NAME_ENDS`   | nothing goes on: no letter, no `@`, no further label    |
# | `REST`        | a port, then a path, a query or a fragment — ending     |
# |               | like any bare address, and never on the `?` or `!` of   |
# |               | the sentence around it                                  |
NOT_INSIDE = r"(?<![^\W_])(?<![@#/.\-])"
WWW_NAME = rf"www\.{LABELS}[A-Za-z]{{2,}}"
LISTED_NAME = rf"{LABELS}(?:{'|'.join(EXTENSIONS)})"
NAME_ENDS = r"(?![^\W_]|[@\-])(?!\.[^\W_])"
REST = r"""(?::[0-9]+)?(?:[/?#][^\s<]*[^<.,:;"'\]\s*_~?!]|/)?"""

PATTERN = rf"{NOT_INSIDE}(?:{WWW_NAME}|{LISTED_NAME}){NAME_ENDS}{REST}"
BARE_DOMAIN = re.compile(PATTERN)


def parse_bare_domain(inline, m, state):
    text = without_a_sentence_parenthesis(m.group(0))
    append_address(inline, state, text, ASSUMED_SCHEME + text)
    return m.start() + len(text)


def bare_domain_plugin(md):
    md.inline.register("bare_domain", PATTERN, parse_bare_domain)


# --- What an output asks of a label ---


def is_bare_domain(label):
    """Whether the whole label is a domain written without its scheme —
    its link's address already, not a name for it."""
    return BARE_DOMAIN.fullmatch(label) is not None


def is_spelled_by(url, label):
    """Whether the label is this address as it was written — itself, or
    less the scheme a bare domain was given."""
    return label in (url, url.removeprefix(ASSUMED_SCHEME))
