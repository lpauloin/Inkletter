// The document as a fragment of HTML, to set inside another page —
// `inkletter/md_to_html_fragment.py`.

import { type AstOptions, parseMarkdownToAst } from './md_to_ast.js';
import { HtmlFragmentCodegen } from './visitors/htmlgen.js';

export type HtmlFragmentOptions = Omit<AstOptions, 'theme'>;

export function parseMarkdownToHtmlFragment(markdownText: string, options: HtmlFragmentOptions = {}): string {
  const codegen = new HtmlFragmentCodegen();
  codegen.visit(parseMarkdownToAst(markdownText, options));
  return codegen.getHtml();
}
