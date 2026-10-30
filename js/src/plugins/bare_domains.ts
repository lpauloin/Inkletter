// A domain written without its scheme — `exemple.com`, `www.exemple.fr/page`
// — read as a link to `https://` plus what was written:
// `inkletter/plugins/bare_domains.py`, where each spelling it reads and
// refuses is laid out. The list of extensions is closed on purpose.

import { SPACE } from '../stdlib.js';

export const EXTENSIONS = [
  'com', 'net', 'org', 'info', 'biz',
  'io', 'co', 'ai', 'app', 'dev', 'tech',
  'fr', 'eu', 'be', 'ch', 'lu', 'ca',
  'uk', 'de', 'es', 'it', 'nl', 'pt', 'us',
] as const;

/** The scheme a domain written without one is given. */
export const ASSUMED_SCHEME = 'https://';

// One label of a host name: unaccented letters and digits, hyphens inside
// only.
const LABEL = '[A-Za-z0-9]+(?:-+[A-Za-z0-9]+)*';
const LABELS = `(?:${LABEL}\\.)+`;

// | Part          | What it holds                                           |
// |---------------|---------------------------------------------------------|
// | `NOT_INSIDE`  | not in a word, a mail address, a tag, a path or a       |
// |               | longer name                                             |
// | `WWW_NAME`    | a name opening on `www.`, whatever its ending           |
// | `LISTED_NAME` | a name ending on an extension of the list               |
// | `NAME_ENDS`   | nothing goes on: no letter, no `@`, no further label    |
// | `REST`        | a port, then a path, a query or a fragment              |
const NOT_INSIDE = '(?<![\\p{L}\\p{N}])(?<![@#/.\\-])';
const WWW_NAME = `www\\.${LABELS}[A-Za-z]{2,}`;
const LISTED_NAME = `${LABELS}(?:${EXTENSIONS.join('|')})`;
const NAME_ENDS = '(?![\\p{L}\\p{N}]|[@\\-])(?!\\.[\\p{L}\\p{N}])';
const REST = `(?::[0-9]+)?(?:[/?#][^${SPACE}<]*[^<.,:;"'\\]${SPACE}*_~?!]|/)?`;

const PATTERN = `${NOT_INSIDE}(?:${WWW_NAME}|${LISTED_NAME})${NAME_ENDS}${REST}`;
/** Read in the text by `bare_links`, with the full address. */
export const BARE_DOMAIN = new RegExp(PATTERN, 'gu');
const WHOLE_BARE_DOMAIN = new RegExp(`^(?:${PATTERN})$`, 'u');

// --- What an output asks of a label ---

/** Whether the whole label is a domain written without its scheme — its
 *  link's address already, not a name for it. */
export function isBareDomain(label: string): boolean {
  return WHOLE_BARE_DOMAIN.test(label);
}

/** Whether the label is this address as it was written — itself, or less
 *  the scheme a bare domain was given. */
export function isSpelledBy(url: string, label: string): boolean {
  return label === url || (url.startsWith(ASSUMED_SCHEME) && label === url.slice(ASSUMED_SCHEME.length));
}
