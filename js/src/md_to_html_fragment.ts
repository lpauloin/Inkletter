// The document as a fragment of HTML, to set inside another page —
// `inkletter/md_to_html_fragment.py`.

import { type AstOptions, parseMarkdownToAst } from './md_to_ast.js';
import { HtmlFragmentCodegen, type MentionAttributes } from './visitors/htmlgen.js';

export type HtmlFragmentOptions = Omit<AstOptions, 'theme'> & {
  /** The pictures drawn, for a page that serves their addresses itself;
   *  their alternative text otherwise. */
  images?: boolean;
  /** The attributes of each mention's anchor, by its URN — an address to a
   *  public page, an entity an editor reads back —; `null`, `undefined`, an
   *  empty object or a set the rules refuse (`anchorAttributes`) for
   *  `@name`. Without it, a mention is its name. */
  mentions?: MentionAttributes | null;
  /** Strikethrough in its Unicode look-alike rather than `<s>`. */
  unicodeStrike?: boolean;
  /** A list holding tasks as a paragraph per item rather than a list. */
  taskParagraphs?: boolean;
};

export function parseMarkdownToHtmlFragment(markdownText: string, options: HtmlFragmentOptions = {}): string {
  const codegen = new HtmlFragmentCodegen(
    options.images ?? false,
    options.mentions ?? null,
    options.unicodeStrike ?? false,
    options.taskParagraphs ?? false,
  );
  // Accents composed first (NFC), as the post composes them: a letter and
  // its accent are one character, which a look-alike strikes as one.
  codegen.visit(parseMarkdownToAst(markdownText.normalize('NFC'), options));
  return codegen.getHtml();
}
