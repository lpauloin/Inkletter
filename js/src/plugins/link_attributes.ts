// Pandoc's `link_attributes`, narrowed to what an email can honour —
// `inkletter/plugins/link_attributes.py`:
//
//     ![Acme](logo@2x.png){width=96px align=left}
//
// A dimension is a fact about the asset; an appearance is a choice of
// theme: width, height and align are accepted, no CSS property ever will
// be. The block decorates the token it is glued to — an image, or a link
// holding one; anything else gives the hand back and the braces stay
// literal text, which is also the author's escape hatch: a single space
// before the brace is enough.

import type MarkdownIt from 'markdown-it';
import type { StateInline, Token } from 'markdown-it';
import { MarkupError } from '../exceptions.js';
import { SPACE, WORD, strip } from '../stdlib.js';

/** The only keys: an unknown one raises, a typo in an email cannot be taken
 *  back once it is sent. */
export const KEYS = ['width', 'height', 'align'] as const;
/** mj-image knows these three. */
export const ALIGNMENTS = ['left', 'center', 'right'] as const;
/** px only, a bare number meaning px. */
const DIMENSION = /^(\p{Nd}+(?:\.\p{Nd}+)?)(px)?$/u;
/** A brace block on one line, matched loosely: what is inside decides
 *  whether it is an attribute block at all. */
const BLOCK = /\{([^{}\n]*)\}/y;
/** One token: key=value, the value optionally quoted. */
const TOKEN = new RegExp(`([A-Za-z][${WORD}-]*)=("[^"]*"|'[^']*'|[^${SPACE}"'{}]+)`, 'gu');

export type ImageAttributes = Partial<Record<(typeof KEYS)[number], string>>;

/** The key/value pairs of a brace block, or null if it is not one. Strict by
 *  design: one malformed token and the whole block stops being one. */
export function parsePairs(body: string): [string, string][] | null {
  const pairs: [string, string][] = [];
  let position = 0;
  for (const match of body.matchAll(TOKEN)) {
    if (strip(body.slice(position, match.index))) return null; // stray text between two tokens
    position = match.index + match[0].length;
    pairs.push([match[1] ?? '', (match[2] ?? '').replace(/^["']+|["']+$/g, '')]);
  }
  if (strip(body.slice(position)) || !pairs.length) return null;
  return pairs;
}

function checkDimension(key: string, value: string): string {
  const match = DIMENSION.exec(value);
  if (!match) throw new MarkupError(`'${key}=${value}' is not a length; mj-image sizes in px only`);
  return `${match[1]}${match[2] ?? 'px'}`;
}

function checkAlign(value: string): string {
  if (!(ALIGNMENTS as readonly string[]).includes(value)) {
    throw new MarkupError(`'align=${value}' is not an alignment; use ${ALIGNMENTS.join(', ')}`);
  }
  return value;
}

function isKey(key: string): key is (typeof KEYS)[number] {
  return (KEYS as readonly string[]).includes(key);
}

/** The validated attributes of a block. Throws on anything else. */
export function build(pairs: [string, string][]): ImageAttributes {
  const attributes: ImageAttributes = {};
  for (const [key, value] of pairs) {
    if (!isKey(key)) {
      throw new MarkupError(
        `unknown image attribute '${key}'; the theme decides how images look. ` +
          `Attributes carry facts about the asset: ${KEYS.join(', ')}.`,
      );
    }
    if (key in attributes) throw new MarkupError(`'${key}' is set twice`);
    attributes[key] = key === 'align' ? checkAlign(value) : checkDimension(key, value);
  }
  return attributes;
}

/** The image the block glued to the last token decorates — that token, or
 *  the image inside the link it closes — or null. */
function imageDecorated(tokens: Token[]): Token | null {
  const last = tokens.at(-1);
  if (!last) return null;
  if (last.type === 'image') return last;
  if (last.type !== 'link_close') return null;
  let depth = 0;
  for (let at = tokens.length - 2; at >= 0; at -= 1) {
    const token = tokens[at];
    if (!token) break;
    if (token.type === 'link_open' && depth === 0) return null;
    depth += token.type === 'link_close' ? 1 : token.type === 'link_open' ? -1 : 0;
    if (token.type === 'image' && depth === 0) return token;
  }
  return null;
}

function attributeBlock(state: StateInline, silent: boolean): boolean {
  if (state.src[state.pos] !== '{') return false;
  // glued to the token before it: a space in between is the author's
  // escape hatch, and Pandoc's
  const image = state.pending ? null : imageDecorated(state.tokens);
  BLOCK.lastIndex = state.pos;
  const match = BLOCK.exec(state.src);
  if (image === null || !match) return false; // give the hand back: the braces stay literal
  const pairs = parsePairs(match[1] ?? '');
  if (pairs === null) return false;
  if (!silent) {
    const attributes = build(pairs);
    // a block written after a link decorates the image it wraps, so both
    // spellings land in the same place — the image's own first
    image.meta = { ink_attributes: attributes, ...image.meta };
  }
  state.pos = BLOCK.lastIndex;
  return true;
}

export function linkAttributesPlugin(md: MarkdownIt): void {
  md.inline.ruler.before('emphasis', 'ink_attrs', attributeBlock);
}
