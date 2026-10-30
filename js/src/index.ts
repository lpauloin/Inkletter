// Inkletter: Markdown to LinkedIn posts, HTML fragments, MJML and responsive
// emails — the JavaScript twin of the Python package, output for output.

export { escapeMarkdown } from './escaping.js';
export { LengthError, MarkupError, ThemeError } from './exceptions.js';
export { type AstOptions, createMarkdown, parseMarkdownToAst, readMarkdown } from './md_to_ast.js';
export { parseMarkdownToHtml, parseMjmlToHtml } from './md_to_html.js';
export { type HtmlFragmentOptions, parseMarkdownToHtmlFragment } from './md_to_html_fragment.js';
export { type LinkedinOptions, parseMarkdownToLinkedin, renderLinkedin } from './md_to_linkedin.js';
export { LinkedinRender } from './visitors/linkedingen.js';
export type { Line, Segment, SegmentKind } from './codeblock.js';
export { BARE_DOMAIN, EXTENSIONS, isBareDomain, isSpelledBy } from './plugins/bare_domains.js';
// The tree and the visitor, for an application that lays a document out its
// own way — an editing surface reading the text as the render reads it.
export * as ast from './ast.js';
export { NodeVisitor } from './visitors/generic.js';
export { ScopeStack } from './visitors/scope.js';
export { type MjmlOptions, parseMarkdownToMjml, wrapMjmlDocument } from './md_to_mjml.js';
export { URLFactory } from './shortener.js';
export { THEMES, Theme, type ThemeMapping, type ThemeOverrides, type ThemeSections } from './theme.js';
export { MAX_LENGTH } from './counting.js';
export type { Document } from './ast.js';
