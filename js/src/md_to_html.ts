// The document as a responsive email — `inkletter/md_to_html.py`. The MJML
// is compiled by MJML's own browser build, `mjml-browser` (which wants
// `cheerio` beside it), loaded only when asked for: it weighs as much as the
// rest of an application. Its HTML is
// not MRML's, which the Python package compiles with: the MJML is the same
// to the character, the HTML each compiler's own.

import { type MjmlOptions, parseMarkdownToMjml } from './md_to_mjml.js';

export async function parseMjmlToHtml(mjmlText: string): Promise<string> {
  const { default: mjml2html } = await import('mjml-browser');
  return (await mjml2html(mjmlText, { validationLevel: 'soft' })).html;
}

export async function parseMarkdownToHtml(markdownText: string, options: MjmlOptions = {}): Promise<string> {
  return parseMjmlToHtml(parseMarkdownToMjml(markdownText, options));
}
