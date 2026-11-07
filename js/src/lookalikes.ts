// Unicode look-alikes of bold, italic and strikethrough — for a text that
// has no formatting of its own: a plain-text destination, a document pasted
// into an editor that keeps no strike — `inkletter/lookalikes.py`. Text, not
// formatting, and asked for by every output that uses them.
//
// | Styles in force  | Letters become                           |
// |------------------|------------------------------------------|
// | bold             | 𝗺𝗼𝘁 𝟮𝟬𝟮𝟲 sans-serif bold, digits too       |
// | italic           | 𝘮𝘰𝘵 sans-serif italic — no italic digit   |
// | bold and italic  | 𝙢𝙤𝙩 𝟮𝟬𝟮𝟲 sans-serif bold italic, the bold  |
// |                  | digits                                   |
// | strikethrough    | a combining stroke after each letter,    |
// |                  | digit, sign or space — never an emoji —  |
// |                  | and after the accents that follow it     |
//
// An accented letter goes out as the look-alike of its letter followed by
// its accents (`𝗲` + U+0301 for `é`), but a capital with an accent above it
// (`É`, `À`) stays as it is — the look-alike's height loses that accent —,
// and a letter whose base is not ASCII (`œ`, `ß`) too.

const ASCII_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
const DIGITS = '0123456789';

function lookalikes(lower: number, upper: number, figures?: number): ReadonlyMap<string, string> {
  const run = (from: number, length: number) => Array.from({ length }, (_, at) => from + at);
  const targets = [...run(lower, 26), ...run(upper, 26), ...(figures === undefined ? [] : run(figures, 10))];
  const sources = figures === undefined ? ASCII_LETTERS : ASCII_LETTERS + DIGITS;
  return new Map([...sources].map((source, at) => [source, String.fromCodePoint(targets[at] ?? 0)]));
}

// The sans-serif bold digits; there are no italic ones.
const BOLD_DIGITS = 0x1d7ec;
const LETTERS: Readonly<Record<string, ReadonlyMap<string, string>>> = {
  bold: lookalikes(0x1d5ee, 0x1d5d4, BOLD_DIGITS),
  italic: lookalikes(0x1d622, 0x1d608),
  'bold italic': lookalikes(0x1d656, 0x1d63c, BOLD_DIGITS),
};
// The combining marks drawn above a letter — grave to the comma above,
// the horn and the left angle above: lost on a capital's look-alike.
const ABOVE = /^[\u0300-\u0315\u031a\u031b]$/u;

/** An accented letter as its ASCII letter and its accents, when its
 *  look-alike keeps them; the letter itself otherwise. */
function decomposed(char: string): string {
  const [letter = '', ...marks] = Array.from(char.normalize('NFD'));
  if (!marks.length || !ASCII_LETTERS.includes(letter)) return char;
  if (letter !== letter.toLowerCase() && marks.some((mark) => ABOVE.test(mark))) return char;
  return letter + marks.join('');
}
const STRIKE = '\u0336';
// What the stroke goes after: letters, digits, punctuation, spaces and the
// like. Not an emoji, nor what an emoji is built of.
const STRUCK = /^[\p{L}\p{N}\p{P}\p{Zs}\p{Sc}\p{Sm}]$/u;
const SPACE_SEPARATOR = /^\p{Zs}$/u;
// What belongs to the character before it — an accent, a vowel sign: the
// stroke goes after them, or it would sit between a letter and its accent.
const COMBINING = /^[\p{Mn}\p{Mc}]$/u;

/** Each character with the combining marks that follow it. */
export function clusters(text: string): string[] {
  const found: string[] = [];
  for (const char of text) {
    if (found.length && COMBINING.test(char)) found[found.length - 1] += char;
    else found.push(char);
  }
  return found;
}

/** A stroke after each character it goes after, past its combining marks —
 *  and not on a space that touches something it skips. `before` and
 *  `after` are the struck text around this one, written apart — another
 *  style, another tag —: read for the neighbours of a space at an edge,
 *  never struck here. */
export function strike(text: string, before = '', after = ''): string {
  const own = clusters(text);
  const edgeBefore = clusters(before).slice(-1);
  const line = [...edgeBefore, ...own, ...clusters(after).slice(0, 1)];
  return own
    .map((cluster, index) => {
      const at = index + edgeBefore.length;
      const base = Array.from(cluster)[0] ?? '';
      let struck = STRUCK.test(base);
      if (struck && SPACE_SEPARATOR.test(base)) {
        struck = [line[at - 1], line[at + 1]].every(
          (neighbour) => neighbour === undefined || STRUCK.test(Array.from(neighbour)[0] ?? ''),
        );
      }
      return struck ? cluster + STRIKE : cluster;
    })
    .join('');
}

/** `text` in the look-alikes of `styles`. */
export function substitute(text: string, styles: ReadonlySet<string>): string {
  const key = ['bold', 'italic'].filter((style) => styles.has(style)).join(' ');
  const letters = LETTERS[key];
  let styled = letters
    ? Array.from(text, decomposed)
        .join('')
        .replace(/./gsu, (char) => letters.get(char) ?? char)
    : text;
  if (styles.has('strikethrough')) styled = strike(styled);
  return styled;
}
