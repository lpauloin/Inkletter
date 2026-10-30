// An address written in the text without brackets — in full or as a domain
// — read as a link to itself: `inkletter/plugins/bare_links.py`.

import type MarkdownIt from 'markdown-it';
import type { StateCore, Token } from 'markdown-it';
import { SPACE } from '../stdlib.js';
import { ASSUMED_SCHEME, BARE_DOMAIN } from './bare_domains.js';

// An address written without brackets, which CommonMark reads as text and
// every reader as a link: read as one, so the URL factory shortens it and
// the counter charges it like any other. It never ends on `*`, `_` or `~`
// (GFM's autolink rule), or `**https://exemple.fr**` would swallow its
// closing marks. A final `)` is matched, and weighed below.
const BARE_URL = new RegExp(`https?:\\/\\/[^${SPACE}<]+[^<.,:;"'\\]${SPACE}*_~]`, 'gu');

// What a token leaves just before the text that follows it, for a rule that
// needs to see what an address is written against: a mark's own spelling,
// and these for the tokens that have none.
const SPELLED_ENDS: Readonly<Record<string, string>> = {
  link_close: ')',
  image: ')',
  code_inline: '`',
  softbreak: '\n',
  hardbreak: '\n',
  hashtag: '#',
};

/** GFM's parenthesis rule: a closing parenthesis at the end belongs to the
 *  address only when an opening one inside it is waiting for it. */
function withoutASentenceParenthesis(text: string): string {
  let kept = text;
  while (kept.endsWith(')') && occurrences(')', kept) > occurrences('(', kept)) kept = kept.slice(0, -1);
  return kept;
}

function occurrences(char: string, value: string): number {
  return value.split(char).length - 1;
}

// A hand-written anchor, opening or closing: what it holds is its label.
const ANCHOR_OPENS = /^<a[\s>]/i;
const ANCHOR_CLOSES = /^<\/a\s*>/i;

/** How far a token takes the text into a link's label, or out of it. */
function linkDepth(token: Token): number {
  if (token.type === 'html_inline' && ANCHOR_OPENS.test(token.content)) return 1;
  if (token.type === 'html_inline' && ANCHOR_CLOSES.test(token.content)) return -1;
  return token.type === 'link_open' ? 1 : token.type === 'link_close' ? -1 : 0;
}

/** Text as the author meant it: written, or an entity spelling a character.
 *  An escaped character is not: `exemple\.com` was written not to be an
 *  address. */
function isText(token: Token): boolean {
  return token.type === 'text' || (token.type === 'text_special' && token.info === 'entity');
}

/** The tokens with each run of text joined into one. */
function runs(state: StateCore, tokens: Token[]): Token[] {
  const joined: Token[] = [];
  for (const token of tokens) {
    const last = joined.at(-1);
    if (isText(token) && last && isText(last)) joined[joined.length - 1] = text(state, last.content + token.content);
    else if (isText(token)) joined.push(text(state, token.content));
    else joined.push(token);
  }
  return joined;
}

function text(state: StateCore, content: string): Token {
  const token = new state.Token('text', '', 0);
  token.content = content;
  return token;
}

function lastChar(value: string): string {
  return Array.from(value).at(-1) ?? '';
}

/** The character the source holds just before `tokens[index]` — what a
 *  lookbehind on an address needs once the text is cut into tokens. */
function spelledBefore(tokens: Token[], index: number): string {
  const previous = tokens[index - 1];
  if (!previous) return '';
  if (previous.type === 'text' || previous.type === 'html_inline') return lastChar(previous.content);
  if (previous.type === 'text_special') return lastChar(previous.markup);
  return SPELLED_ENDS[previous.type] ?? lastChar(previous.markup);
}

interface Address {
  start: number;
  written: string;
  url: string;
}

/** The first bare address of `value` at or after `position`. A full address
 *  wins a tie with a domain inside it. */
function nextAddress(value: string, position: number): Address | null {
  let best: { start: number; written: string; scheme: string } | null = null;
  for (const [pattern, scheme] of [
    [BARE_URL, ''],
    [BARE_DOMAIN, ASSUMED_SCHEME],
  ] as const) {
    pattern.lastIndex = position;
    const match = pattern.exec(value);
    if (match && (best === null || match.index < best.start)) best = { start: match.index, written: match[0], scheme };
  }
  if (best === null) return null;
  const written = withoutASentenceParenthesis(best.written);
  return { start: best.start, written, url: best.scheme + written };
}

/** A text token cut at its bare addresses: the text between them, and each
 *  address as a link labelled with what was written. */
function linked(state: StateCore, token: Token, before: string): Token[] {
  const value = before + token.content;
  let position = before.length;
  const cut: Token[] = [];
  for (let address = nextAddress(value, position); address; address = nextAddress(value, position)) {
    const { start, written, url } = address;
    if (start > position) cut.push(text(state, value.slice(position, start)));
    const opening = new state.Token('link_open', 'a', 1);
    opening.attrs = [['href', state.md.normalizeLink(url)]];
    cut.push(opening, text(state, written), new state.Token('link_close', 'a', -1));
    position = start + written.length;
  }
  if (!cut.length) return [token];
  if (position < value.length) cut.push(text(state, value.slice(position)));
  return cut;
}

/** Reads the bare addresses of every run of text — but inside a link's
 *  label, written in Markdown or by hand, which holds no link. */
function bareLinks(state: StateCore): void {
  for (const block of state.tokens) {
    if (block.type !== 'inline' || !block.children) continue;
    const tokens = runs(state, block.children);
    const children: Token[] = [];
    let depth = 0;
    tokens.forEach((token, index) => {
      depth += linkDepth(token);
      if (token.type === 'text' && depth === 0) children.push(...linked(state, token, spelledBefore(tokens, index)));
      else children.push(token);
    });
    block.children = children;
  }
}

export function bareLinksPlugin(md: MarkdownIt): void {
  // before the escapes join the text around them: an escaped character is
  // not part of an address
  md.core.ruler.before('text_join', 'bare_links', bareLinks);
}
