// Making a value literal once it lands in a Markdown document —
// `inkletter/escaping.py`: every ASCII punctuation character, which
// CommonMark allows to be backslash-escaped.

const PUNCTUATION = /([!-/:-@[-`{-~])/g;

/** `value` so that Markdown reads it as plain text. */
export function escapeMarkdown(value: string): string {
  return String(value).replace(PUNCTUATION, '\\$1');
}
