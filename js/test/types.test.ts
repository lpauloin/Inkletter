// The types a caller writes against, checked by the typecheck (`npm run
// typecheck` reads the tests): the declarations published with the package
// say what each call takes and gives.

import { expectTypeOf, test } from 'vitest';
import {
  type Document,
  type HtmlFragmentOptions,
  type Line,
  type Segment,
  LengthError,
  type LinkedinRender,
  MAX_LENGTH,
  type MjmlOptions,
  parseMarkdownToAst,
  parseMarkdownToHtml,
  parseMarkdownToHtmlFragment,
  parseMarkdownToLinkedin,
  parseMarkdownToMjml,
  renderLinkedin,
  Theme,
  type ThemeMapping,
  URLFactory,
} from '../src/index.js';

test('each output takes a string and its options, and gives what it renders', () => {
  expectTypeOf(renderLinkedin).returns.toEqualTypeOf<LinkedinRender>();
  expectTypeOf(renderLinkedin('a').text).toEqualTypeOf<string>();
  expectTypeOf(renderLinkedin('a').shownText).toEqualTypeOf<string>();
  expectTypeOf(renderLinkedin('a').lines).toEqualTypeOf<readonly Line[]>();
  expectTypeOf<Segment['kind']>().toEqualTypeOf<'text' | 'mention' | 'hashtag' | 'link'>();
  expectTypeOf(renderLinkedin('a').unrenderedFormatting).toEqualTypeOf<boolean>();
  expectTypeOf(parseMarkdownToLinkedin).returns.toEqualTypeOf<string>();
  expectTypeOf(parseMarkdownToHtmlFragment).parameter(1).toEqualTypeOf<HtmlFragmentOptions | undefined>();
  expectTypeOf(parseMarkdownToHtmlFragment).returns.toEqualTypeOf<string>();
  expectTypeOf(parseMarkdownToMjml).parameter(1).toEqualTypeOf<MjmlOptions | undefined>();
  expectTypeOf(parseMarkdownToMjml).returns.toEqualTypeOf<string>();
  expectTypeOf(parseMarkdownToHtml).returns.toEqualTypeOf<Promise<string>>();
  expectTypeOf(parseMarkdownToAst).returns.toEqualTypeOf<Document>();
  expectTypeOf(MAX_LENGTH).toEqualTypeOf<number>();
});

test('a theme is built from the mapping of a theme file', () => {
  expectTypeOf(Theme.fromDict).parameter(0).toEqualTypeOf<ThemeMapping>();
  expectTypeOf(Theme.named).returns.toEqualTypeOf<Theme>();
  expectTypeOf<MjmlOptions['theme']>().toEqualTypeOf<Theme | null | undefined>();
});

test('a factory says the width of its links and rewrites them', () => {
  expectTypeOf<URLFactory['linkLength']>().toEqualTypeOf<number | null>();
  expectTypeOf<URLFactory['rewriteLink']>().toEqualTypeOf<(url: string, isButton: boolean, isBold: boolean) => string>();
  expectTypeOf<LengthError['length']>().toEqualTypeOf<number>();
});
