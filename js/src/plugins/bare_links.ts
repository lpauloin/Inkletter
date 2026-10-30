// An address written in the text without brackets — in full or as a domain
// — read as a link to itself: `inkletter/plugins/bare_links.py`.
//
// | Written                | Rule                                                 |
// |------------------------|------------------------------------------------------|
// | `https://exemple.fr/…` | inline, at its `:` — read whole before any mark, so  |
// |                        | `https://a.fr/*x*` keeps its stars (markdown-it's    |
// |                        | own linkify rule works the same way)                 |
// | `exemple.fr/…`         | core, in the text once its marks are read: nothing   |
// |                        | announces a domain to an inline rule                 |

import type MarkdownIt from 'markdown-it';
import type { StateCore, StateInline, Token } from 'markdown-it';
import { SPACE } from '../stdlib.js';
import { ASSUMED_SCHEME, DOMAIN_PATTERN } from './bare_domains.js';

// The domains of a run of text, searched from a position.
const DOMAINS = new RegExp(DOMAIN_PATTERN, 'gu');

// An address written without brackets, read as a link so the URL factory
// shortens it and the counter charges it like any other. Where it starts and
// ends is LinkedIn's, measured in its own composer and laid out in
// `inkletter/plugins/bare_links.py`: after a space, the start, `(`, `"` or a
// mark; never ending on the sentence's sign (`.,:;"'?!]`) nor on a mark.
const BARE_URL = new RegExp(`(?<![^${SPACE}(*_~"])https?:\\/\\/[^${SPACE}<]+[^<.,:;"'\\]${SPACE}*_~?!]`, 'uy');
// The scheme the text before a `:` ends on.
const SCHEME = /https?$/;

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

/** The character the source holds just before `tokens[index]`, when the
 *  domain's lookbehind needs it: the end of a text, or an escaped character
 *  (`\.exemple.com` is no domain). Every other token ends on a sign the
 *  lookbehind lets by. */
function spelledBefore(tokens: Token[], index: number): string {
  const previous = tokens[index - 1];
  if (!previous) return '';
  if (previous.type === 'text' || previous.type === 'html_inline') return lastChar(previous.content);
  if (previous.type === 'text_special') return lastChar(previous.markup);
  return '';
}

// --- In full: inline, at its `:` ---

/** The inline state as markdown-it fills it: its types leave out
 *  `linkLevel`, how deep the text sits in a link's label — the guard its own
 *  linkify rule reads. */
type LinkAwareState = StateInline & { linkLevel: number };

/** An address in full, read when the text reaches its `:` — its scheme
 *  already written, waiting to be taken back. */
function bareUrl(state: StateInline, silent: boolean): boolean {
  if ((state as LinkAwareState).linkLevel > 0 || !state.src.startsWith('://', state.pos)) return false;
  const scheme = SCHEME.exec(state.pending)?.[0];
  if (scheme === undefined) return false;
  const start = state.pos - scheme.length;
  BARE_URL.lastIndex = start;
  const match = BARE_URL.exec(state.src);
  if (!match) return false;
  const written = withoutASentenceParenthesis(match[0]);
  if (!silent) {
    state.pending = state.pending.slice(0, -scheme.length);
    // its entities read, like the text around it
    const url = state.md.utils.unescapeAll(written);
    state.push('link_open', 'a', 1).attrs = [['href', state.md.normalizeLink(url)]];
    state.push('text', '', 0).content = url;
    state.push('link_close', 'a', -1);
  }
  state.pos = start + written.length;
  return true;
}

// --- As a domain: in the text, once its marks are read ---

interface Address {
  start: number;
  written: string;
  url: string;
}

/** The first domain of `value` at or after `position`. */
function nextAddress(value: string, position: number): Address | null {
  DOMAINS.lastIndex = position;
  const match = DOMAINS.exec(value);
  if (!match) return null;
  const written = withoutASentenceParenthesis(match[0]);
  return { start: match.index, written, url: ASSUMED_SCHEME + written };
}

/** A text token cut at its domains: the text between them, and each domain
 *  as a link labelled with what was written. */
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

/** Reads the domains of every run of text — but inside a link's label,
 *  written in Markdown or by hand, which holds no link. */
function bareDomains(state: StateCore): void {
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
  md.inline.ruler.before('linkify', 'bare_url', bareUrl);
  // before the escapes join the text around them: an escaped character is
  // not part of an address
  md.core.ruler.before('text_join', 'bare_domains', bareDomains);
}
