// A list ends where its author stopped writing it —
// `inkletter/plugins/typed_lists.py`: inside an item, a line short of the
// item's indent ends the item's paragraph, and the list rule ends the list
// there. No lazy continuation.

import type MarkdownIt from 'markdown-it';
import type { StateBlock } from 'markdown-it';

/** Ends a paragraph, inside an item, at a line written short of the item's
 *  indent. */
function typedListEnd(state: StateBlock, line: number, _end: number, silent: boolean): boolean {
  return silent && state.blkIndent > 0 && (state.sCount[line] ?? 0) < state.blkIndent;
}

export function typedListsPlugin(md: MarkdownIt): void {
  md.block.ruler.before('paragraph', 'typed_list_end', typedListEnd, { alt: ['paragraph'] });
}
