// `#tag`, read as a hashtag before any mark inside it —
// `inkletter/plugins/hashtags.py`.

import type MarkdownIt from 'markdown-it';
import type { StateInline } from 'markdown-it';
import { WORD } from '../stdlib.js';

// A hashtag as LinkedIn reads one — measured in its own composer, laid out
// in `inkletter/plugins/hashtags.py`: `#`, then letters, digits or
// underscores, not after an ASCII letter or digit, `_`, `&` or `/`.
const PATTERN = `(?<![A-Za-z0-9_&/])#[${WORD}]+`;
/** A hashtag, for an application to search a text with. */
export const HASHTAG = new RegExp(PATTERN, 'u');
// read where the inline rule stands
const HASHTAG_HERE = new RegExp(PATTERN, 'uy');

function hashtag(state: StateInline, silent: boolean): boolean {
  if (state.src[state.pos] !== '#') return false;
  HASHTAG_HERE.lastIndex = state.pos;
  const match = HASHTAG_HERE.exec(state.src);
  if (!match) return false;
  if (!silent) {
    const token = state.push('hashtag', '', 0);
    token.meta = { name: match[0].slice(1) };
  }
  state.pos = HASHTAG_HERE.lastIndex;
  return true;
}

export function hashtagPlugin(md: MarkdownIt): void {
  md.inline.ruler.before('emphasis', 'hashtag', hashtag);
}
