"""`#tag`, read as a hashtag before any mark inside it."""

import re

# A hashtag as LinkedIn reads one — measured in its own composer: `#`, then
# letters, digits or underscores, read before the marks inside it, so that
# `#équipe_rh` is one tag where the emphasis rule would have seen an `_` to
# open an italic. Not a heading: a heading is a block, decided line by line
# before any inline rule runs, and it needs a space after its `#`.
#
# | Before the `#`                              | A tag?                    |
# |---------------------------------------------|---------------------------|
# | a space, the start, `(`, `-`, `.`, `@`      | yes                       |
# | another `#` (`##tag`), an accented letter   | yes                       |
# | an ASCII letter or digit, `_`, `&`, `/`     | no: `C#`, `2#a`, `&#35;`  |
#
# A number is a tag (`#2026`), as on the feed.
HASHTAG = re.compile(r"(?<![A-Za-z0-9_&/])#\w+")


def hashtag(state, silent):
    if state.src[state.pos] != "#":
        return False
    match = HASHTAG.match(state.src, state.pos)
    if match is None:
        return False
    if not silent:
        token = state.push("hashtag", "", 0)
        token.meta = {"name": match.group(0)[1:]}
    state.pos = match.end()
    return True


def hashtag_plugin(md):
    md.inline.ruler.before("emphasis", "hashtag", hashtag)
