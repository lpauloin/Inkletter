// The document as a responsive email — `inkletter/md_to_html.py`. The MJML
// is compiled by MJML's own browser build, `mjml-browser` (which wants
// `cheerio` beside it), loaded only when asked for: it weighs as much as the
// rest of an application. Its HTML is
// not MRML's, which the Python package compiles with: the MJML is the same
// to the character, the HTML each compiler's own.

import { type MjmlOptions, parseMarkdownToMjml } from './md_to_mjml.js';

// An MJML tag — the author's words cannot open one, their `<` escaped — and,
// in it, a font family or an mj-font's name: where a font's quotes sit.
const MJML_TAG = /<mj-[^>]*>/g;
const FONT_ATTRIBUTE = /(\s)(font-family|name)="([^"]*)"/g;
const ESCAPED_QUOTE = /&#x27;|&quot;/g;

/** The quotes of a font stack as `mjml-browser` reads them. Its CSS inliner
 *  breaks on an escaped one — a stack such as `'Helvetica Neue', Arial` —
 *  so the stack reaches it with plain apostrophes, which a double-quoted
 *  attribute holds and CSS reads the same. */
function plainFontQuotes(mjmlText: string): string {
  return mjmlText.replace(MJML_TAG, (tag) =>
    tag.replace(
      FONT_ATTRIBUTE,
      (_whole, space: string, attribute: string, value: string) =>
        `${space}${attribute}="${value.replace(ESCAPED_QUOTE, "'")}"`,
    ),
  );
}

export async function parseMjmlToHtml(mjmlText: string): Promise<string> {
  const { default: mjml2html } = await import('mjml-browser');
  return (await mjml2html(plainFontQuotes(mjmlText), { validationLevel: 'soft' })).html;
}

export async function parseMarkdownToHtml(markdownText: string, options: MjmlOptions = {}): Promise<string> {
  return parseMjmlToHtml(parseMarkdownToMjml(markdownText, options));
}
