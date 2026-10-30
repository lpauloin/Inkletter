"""A list ends where its author stopped writing it.

CommonMark reads into a list a line its author never put there: a line
written right after an item, without a marker — lazy continuation makes it
part of the item (`- Étapes` then `Après` reads as one item, "Étapes
Après"). Here it ends the list and starts its own block, as it was typed: a
post, a mail and a page show the list, then the line.

One rule does it, among those that may end a paragraph: inside an item, a
line short of the item's indent ends the item's paragraph, and the list
rule — which only goes on at the item's indent or at a marker — ends the
list there. Everything else is markdown-it's own: item markers, nesting,
tight and loose lists, a list that interrupts a paragraph.

The blank lines after the last item are the document's, not the list's:
`ASTBuilder` counts them between the list and what follows.
"""


def typed_list_end(state, line, end, silent):
    """Ends a paragraph, inside an item, at a line written short of the
    item's indent."""
    return silent and state.blkIndent > 0 and state.sCount[line] < state.blkIndent


def typed_lists_plugin(md):
    md.block.ruler.before("paragraph", "typed_list_end", typed_list_end, {"alt": ["paragraph"]})
