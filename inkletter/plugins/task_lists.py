"""GitHub's task list: `[ ]` or `[x]` opening a list item."""

import re

# `[ ]` or `[x]` opening an item, then a space: GitHub's task list.
TASK = re.compile(r"\[([ xX])\]\s+")


def task_lists(state):
    """Marks an item opening on a box, and takes the box off its text."""
    tokens = state.tokens
    for index, token in enumerate(tokens[:-2]):
        if token.type != "list_item_open" or tokens[index + 1].type != "paragraph_open":
            continue
        text = tokens[index + 2]
        match = TASK.match(text.content)
        if match:
            token.meta["checked"] = match.group(1) != " "
            text.content = text.content[match.end() :]


def task_lists_plugin(md):
    # between the blocks and their text: the box is taken off before the
    # text is read
    md.core.ruler.after("block", "task_lists", task_lists)
