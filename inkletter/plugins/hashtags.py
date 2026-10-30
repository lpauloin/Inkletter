"""`#tag`, read as a hashtag before any mark inside it."""

import re

# A hashtag, read before the marks inside it: `#équipe_rh` is one tag, where
# the emphasis rule would have seen an `_` to open an italic. Not a heading:
# a heading is a block, decided line by line before any inline rule runs,
# and it needs a space after its `#`. Not after a word character, `&` (an
# entity) or another `#` either.
HASHTAG = re.compile(r"(?<![\w&#])#(?=\w*[^\W\d_])\w+")


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
