// GitHub's task list: `[ ]` or `[x]` opening a list item —
// `inkletter/plugins/task_lists.py`.

import type MarkdownIt from 'markdown-it';
import type { StateCore } from 'markdown-it';
import { SPACE } from '../stdlib.js';

// `[ ]` or `[x]` opening an item, then a space: GitHub's task list.
const TASK = new RegExp(`^\\[([ xX])\\][${SPACE}]+`, 'u');

/** Marks an item opening on a box, and takes the box off its text. */
function taskLists(state: StateCore): void {
  const tokens = state.tokens;
  tokens.slice(0, -2).forEach((token, index) => {
    const text = tokens[index + 2];
    if (token.type !== 'list_item_open' || tokens[index + 1]?.type !== 'paragraph_open' || !text) return;
    const match = TASK.exec(text.content);
    if (match) {
      token.meta = { ...token.meta, checked: match[1] !== ' ' };
      text.content = text.content.slice(match[0].length);
    }
  });
}

export function taskListsPlugin(md: MarkdownIt): void {
  // between the blocks and their text: the box is taken off before the
  // text is read
  md.core.ruler.after('block', 'task_lists', taskLists);
}
