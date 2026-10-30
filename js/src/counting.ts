// What a LinkedIn post costs, in the unit the platform counts —
// `inkletter/counting.py`. Measured against the platform's own refusal: it
// counts UTF-16 code units — JavaScript's own `length`. The count is
// accumulated as the document is rendered, never taken over the finished
// string: a mention weighs the name it displays, a link the short link it
// will become.

/** What the platform accepts, measured: beyond this it refuses the text. */
export const MAX_LENGTH = 4000;

/** The unit LinkedIn counts in. */
export function utf16Length(text: string): number {
  return text.length;
}

/** Ordinary text: what it says. */
export function costOfText(text: string): number {
  return utf16Length(text);
}

/** A mention: the name the platform displays, never the marker. */
export function costOfMention(name: string): number {
  return utf16Length(name);
}

/** A link: the width of the short link it will become, when whoever
 *  shortens says what that width is; the address as written otherwise. */
export function costOfLink(url: string, linkLength: number | null = null): number {
  return linkLength === null ? utf16Length(url) : linkLength;
}
