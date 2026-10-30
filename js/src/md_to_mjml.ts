// The document as MJML — `inkletter/md_to_mjml.py`.

import { Document } from './ast.js';
import { type CodeBlock, codeblockFromString } from './codeblock.js';
import { type AstOptions, parseMarkdownToAst } from './md_to_ast.js';
import { DEFAULT_THEME } from './theme.js';
import { Annotation } from './visitors/annotation.js';
import { Codegen } from './visitors/codegen.js';

export type MjmlOptions = AstOptions;

export function parseMarkdownToMjml(markdownText: string, options: MjmlOptions = {}): string {
  const codegen = new Codegen();
  codegen.visit(parseMarkdownToAst(markdownText, options));
  return codegen.getCode();
}

/** Raw body content (sections) wrapped in the default-themed document: the
 *  head and body attributes come from the real Annotation pass on an empty
 *  Document. */
export function wrapMjmlDocument(bodyContent: string | CodeBlock, title: string | null = null): string {
  const content = typeof bodyContent === 'string' ? codeblockFromString(bodyContent) : bodyContent;
  const document = new Document([]);
  new Annotation(DEFAULT_THEME).visit(document);
  const head = document.head;
  if (head === null) throw new Error('an annotated document has a head');
  head.title = title;
  const codegen = new Codegen();
  codegen.blockTag('mjml', null, {}, () => {
    codegen.emitHead(head);
    codegen.blockTag('mj-body', document.annotations.body_attrs as Record<string, string>, {}, () =>
      codegen.current.addCodeblock(content),
    );
  });
  return codegen.getCode();
}
