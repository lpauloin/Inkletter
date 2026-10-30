// The LinkedIn output: a Markdown document rendered as a post —
// `inkletter/md_to_linkedin.py`. One document in, one text out; it never
// publishes, never looks a mention up, and never truncates: a post over the
// ceiling throws rather than leaving cut mid-sentence.

import { MAX_LENGTH } from './counting.js';
import { LengthError } from './exceptions.js';
import { parseMarkdownToAst } from './md_to_ast.js';
import type { URLFactory } from './shortener.js';
import { LinkedinCodegen, type LinkedinRender } from './visitors/linkedingen.js';

export interface LinkedinOptions {
  unicodeStyling?: boolean;
  urlFactory?: URLFactory | null;
  maxLength?: number | null;
}

/** The post, what the platform counts for it, and what a feed shows of it
 *  line by line — refused by no ceiling: the caller weighs it. */
export function renderLinkedin(markdownText: string, options: Omit<LinkedinOptions, 'maxLength'> = {}): LinkedinRender {
  const { unicodeStyling = false, urlFactory = null } = options;
  // Composed accents, always: the platform counts a decomposed one as two
  // units and shows it as one.
  const composed = markdownText.normalize('NFC');
  // No button on a feed: a bold link stays a bold link, and reaches the
  // factory as one.
  const ast = parseMarkdownToAst(composed, { boldLinkIsButton: false, urlFactory });
  return new LinkedinCodegen(unicodeStyling, urlFactory?.linkLength ?? null).render(ast);
}

/** The post, refused over `maxLength` rather than cut. */
export function parseMarkdownToLinkedin(markdownText: string, options: LinkedinOptions = {}): string {
  const { maxLength = MAX_LENGTH } = options;
  const render = renderLinkedin(markdownText, options);
  if (maxLength !== null && render.length > maxLength) throw new LengthError(render.length, maxLength);
  return render.text;
}
