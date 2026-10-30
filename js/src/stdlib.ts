// What Python's standard library answers, in its own terms: the Python
// package is the reference, and every output must fall on its characters.
//
// | Python                   | Here                | Why it is not the JS built-in       |
// |--------------------------|---------------------|-------------------------------------|
// | `len(s)`                 | `codePoints`        | `length` counts UTF-16 units         |
// | `\s`, `str.strip()`      | `SPACE`, `strip`    | `\s` and `trim` hold `﻿`, miss  |
// |                          |                     | `\x1c`–`\x1f` and `\x85`             |
// | `\w`                     | `WORD`              | `\w` is ASCII                        |
// | `str.splitlines()`       | `splitLines`        | eight more line separators           |
// | `str.center` and co.     | `center`, `ljust`…  | padding counted in code points       |
// | `html.escape`            | `htmlEscape`        | not in the language                  |
// | `urllib.parse.quote`     | `quote`             | `encodeURI` keeps another set        |
// | `urllib.parse.unquote`   | `unquote`           | `decodeURIComponent` throws on a     |
// |                          |                     | stray `%`, Python leaves it          |
// | `urllib.parse.urlsplit`  | `urlSplit`          | `URL` refuses what has no scheme     |
// | `f"{x:g}"`               | `formatG`           | not in the language                  |
//
// The letters, digits and spaces are read through Unicode's tables, which
// each runtime carries in its own version: a character only the newer one
// assigns may be a letter on one side and nothing on the other.

/** The characters `str.isspace()` holds true for, as a regex class body. */
export const SPACE = '\\t\\n\\v\\f\\r\\x1c-\\x20\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000';
/** Python's `\w` on a `str`: letters, digits and numbers, the underscore. */
export const WORD = '\\p{L}\\p{N}_';

const LEADING_SPACE = new RegExp(`^[${SPACE}]+`, 'u');
const TRAILING_SPACE = new RegExp(`[${SPACE}]+$`, 'u');

export function strip(text: string): string {
  return rstrip(lstrip(text));
}

export function lstrip(text: string): string {
  return text.replace(LEADING_SPACE, '');
}

export function rstrip(text: string): string {
  return text.replace(TRAILING_SPACE, '');
}

/** `len(text)`: one per code point. */
export function codePoints(text: string): number {
  let count = 0;
  for (const _ of text) count += 1;
  return count;
}

const LINE_SEPARATOR = new RegExp('\\r\\n|[\\n\\r\\v\\f\\x1c\\x1d\\x1e\\x85\\u2028\\u2029]');

/** `str.splitlines()`: no last empty line for a text that ends on a break. */
export function splitLines(text: string): string[] {
  if (!text) return [];
  const lines = text.split(LINE_SEPARATOR);
  if (lines.at(-1) === '') lines.pop();
  return lines;
}

export function ljust(value: string, width: number): string {
  return value + ' '.repeat(Math.max(width - codePoints(value), 0));
}

export function rjust(value: string, width: number): string {
  return ' '.repeat(Math.max(width - codePoints(value), 0)) + value;
}

/** `str.center`: the odd space goes left when the width is odd. */
export function center(value: string, width: number): string {
  const margin = width - codePoints(value);
  if (margin <= 0) return value;
  const left = Math.floor(margin / 2) + (margin & width & 1);
  return ' '.repeat(left) + value + ' '.repeat(margin - left);
}

/** `html.escape`: `&`, `<`, `>`, and the quotes when asked. */
export function htmlEscape(text: string, quote = true): string {
  const escaped = text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  return quote ? escaped.replaceAll('"', '&quot;').replaceAll("'", '&#x27;') : escaped;
}

const ALWAYS_SAFE = /[A-Za-z0-9_.\-~]/;
const ENCODER = new TextEncoder();

/** `urllib.parse.quote`: every UTF-8 octet percent-encoded, but letters,
 *  digits, `_.-~` and the characters of `safe`. */
export function quote(text: string, safe: string): string {
  let quoted = '';
  for (const char of text) {
    if (ALWAYS_SAFE.test(char) || safe.includes(char)) {
      quoted += char;
      continue;
    }
    for (const byte of ENCODER.encode(char)) quoted += `%${byte.toString(16).toUpperCase().padStart(2, '0')}`;
  }
  return quoted;
}

const ESCAPES = /(%[0-9A-Fa-f]{2})+/g;
const DECODER = new TextDecoder('utf-8');

/** `urllib.parse.unquote`: each run of `%xx` decoded as UTF-8, an invalid
 *  sequence as U+FFFD, a stray `%` left as it is. */
export function unquote(text: string): string {
  return text.replace(ESCAPES, (run) => {
    const bytes = Uint8Array.from(run.slice(1).split('%'), (pair) => Number.parseInt(pair, 16));
    return DECODER.decode(bytes);
  });
}

export interface SplitUrl {
  scheme: string;
  path: string;
}

/** `urllib.parse.urlsplit`, for the scheme and the path — or null where it
 *  raises (an unclosed IPv6 bracket). A scheme is a letter, then letters,
 *  digits, `+`, `-` or `.`, before the first `:`. */
export function urlSplit(url: string): SplitUrl | null {
  const cleaned = url.replace(/^[\x00-\x20]+/, '').replace(/[\t\r\n]/g, '');
  const colon = cleaned.indexOf(':');
  let scheme = '';
  let rest = cleaned;
  if (colon > 0 && /^[A-Za-z][A-Za-z0-9+\-.]*$/.test(cleaned.slice(0, colon))) {
    scheme = cleaned.slice(0, colon).toLowerCase();
    rest = cleaned.slice(colon + 1);
  }
  if (rest.startsWith('//')) {
    const end = rest.slice(2).search(/[/?#]/);
    const netloc = end < 0 ? rest.slice(2) : rest.slice(2, end + 2);
    if (netloc.includes('[') !== netloc.includes(']')) return null;
    rest = end < 0 ? '' : rest.slice(end + 2);
  }
  return { scheme, path: rest.split(/[?#]/, 1)[0] ?? '' };
}

/** `f"{value:g}"`, for the numbers a theme holds: six significant digits,
 *  no trailing zero. */
export function formatG(value: number): string {
  return String(Number(value.toPrecision(6)));
}
