// `#tag`, read as a hashtag before any mark inside it —
// `inkletter/plugins/hashtags.py`.

import type MarkdownIt from 'markdown-it';
import type { StateInline } from 'markdown-it';
import { WORD } from '../stdlib.js';

// A hashtag, read before the marks inside it: `#équipe_rh` is one tag, where
// the emphasis rule would have seen an `_` to open an italic. Not a heading:
// a heading is a block, decided line by line before any inline rule runs,
// and it needs a space after its `#`. Not after a word character, `&` (an
// entity) or another `#` either.
const HASHTAG = new RegExp(`(?<![${WORD}&#])#(?=[${WORD}]*[\\p{L}\\p{Nl}\\p{No}])[${WORD}]+`, 'uy');

function hashtag(state: StateInline, silent: boolean): boolean {
  if (state.src[state.pos] !== '#') return false;
  HASHTAG.lastIndex = state.pos;
  const match = HASHTAG.exec(state.src);
  if (!match) return false;
  if (!silent) {
    const token = state.push('hashtag', '', 0);
    token.meta = { name: match[0].slice(1) };
  }
  state.pos = HASHTAG.lastIndex;
  return true;
}

export function hashtagPlugin(md: MarkdownIt): void {
  md.inline.ruler.before('emphasis', 'hashtag', hashtag);
}
