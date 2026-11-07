// The fragment, for a page or an editor that wants a document written its
// way: what the parity scenarios hold, said here once on this side, and what
// only a JavaScript caller can do — a function returning `undefined`.

import { describe, expect, test } from 'vitest';
import { parseMarkdownToHtmlFragment } from '../src/index.js';
import { strike } from '../src/lookalikes.js';

const table = new Map([['urn:li:organization:1', { href: 'https://exemple.fr/a' }]]);

describe('mentions', () => {
  test('a function returning undefined leaves the name as plain text', () => {
    const actual = parseMarkdownToHtmlFragment('[A](urn:li:organization:1) [B](urn:li:organization:2)', {
      mentions: (urn) => table.get(urn),
    });
    expect(actual).toBe('<p><a href="https://exemple.fr/a">A</a> @B</p>');
  });

  test.each([
    ['no attributes at all', {}],
    ['an address that runs something, however spelled', { href: '  JaVa\tScRiPt:alert(1)' }],
    ['an address named in capitals', { HREF: 'javascript:alert(1)' }],
    ['an event handler', { href: 'https://exemple.fr', onclick: 'alert(1)' }],
    ['a name that is no name', { 'x onmouseover=alert(1) y': '1' }],
    ['a name with a colon', { 'xlink:href': 'https://exemple.fr' }],
    ['a source that runs something', { src: 'data:text/html,<script>alert(1)</script>' }],
    ['a name given twice', { href: 'https://exemple.fr', HREF: 'https://exemple.fr' }],
    ['a value that is no string', { 'data-n': 3 } as unknown as Record<string, string>],
  ])('%s leaves the name as plain text', (_, attributes) => {
    const actual = parseMarkdownToHtmlFragment('Bravo [Acme](urn:li:organization:1) !', { mentions: () => attributes });
    expect(actual).toBe('<p>Bravo @Acme !</p>');
  });

  test('a name is written lower-cased, its value escaped', () => {
    const actual = parseMarkdownToHtmlFragment('[Acme](urn:li:organization:1)', {
      mentions: () => ({ 'Data-Entity': 'a"b<c>' }),
    });
    expect(actual).toBe('<p><a data-entity="a&quot;b&lt;c&gt;">Acme</a></p>');
  });
});

describe('strikethrough as its look-alike', () => {
  test('the space beside an emoji in another style stays unstruck', () => {
    expect(parseMarkdownToHtmlFragment('~~salut **👋** toi~~', { unicodeStrike: true })).toBe(
      '<p>s̶a̶l̶u̶t̶ <strong>👋</strong> t̶o̶i̶</p>',
    );
  });

  test('code inside it stays as written', () => {
    expect(parseMarkdownToHtmlFragment('~~un `code` ici~~', { unicodeStrike: true })).toContain('<code>code</code>');
  });

  test('accents are composed before they are struck', () => {
    expect(parseMarkdownToHtmlFragment('~~été~~', { unicodeStrike: true })).toBe(
      '<p>é̶t̶é̶</p>',
    );
  });

  test('the stroke goes after a letter and its accent', () => {
    expect(strike('q̃')).toBe('q̶̃');
  });

  test('a space at an edge reads the text written around it', () => {
    expect(strike('a ', '', '👋')).toBe('a̶ ');
    expect(strike('a ', '', 'b')).toBe('a̶ ̶');
  });
});

describe('lists of tasks as paragraphs', () => {
  test('a plain item of a loose list keeps its marker', () => {
    expect(parseMarkdownToHtmlFragment('- [ ] a\n\n- b\n\n- [x] c', { taskParagraphs: true })).toBe(
      '<p>☐ a</p><p>• b</p><p>☑ c</p>',
    );
  });

  test('a numbered list counts from zero when it starts there', () => {
    expect(parseMarkdownToHtmlFragment('0. [ ] a\n1. b', { taskParagraphs: true })).toBe('<p>☐ a</p><p>1. b</p>');
  });
});

describe('pictures, when asked for', () => {
  test('a title of spaces alone writes no caption', () => {
    expect(parseMarkdownToHtmlFragment('![Plan](https://x.com/p.png "   ")', { images: true })).toBe(
      '<figure><img src="https://x.com/p.png" alt="Plan"></figure>',
    );
  });

  test('a row mixing drawn and undrawn images keeps them apart', () => {
    const actual = parseMarkdownToHtmlFragment(
      '![A](https://x.com/a.png) ![Plan](plan.png) ![](other.png) ![C](https://x.com/c.png)',
      { images: true },
    );
    expect(actual).toBe('<p><img src="https://x.com/a.png" alt="A"> Plan <img src="https://x.com/c.png" alt="C"></p>');
  });

  test('a linked image beside its text keeps its figure', () => {
    const actual = parseMarkdownToHtmlFragment(
      '[![Plan](https://x.com/p.png "Lundi"){size=small}](https://example.com) The plan.',
      { images: true },
    );
    expect(actual).toBe(
      '<figure data-size="small"><a href="https://example.com"><img src="https://x.com/p.png" alt="Plan"></a>' +
        '<figcaption>Lundi</figcaption></figure><p>The plan.</p>',
    );
  });

  test('a picture inside the page is drawn only in a format the tree accepts', () => {
    expect(parseMarkdownToHtmlFragment('![Plan](data:image/svg+xml;base64,PHN2Zz4=)', { images: true })).not.toContain(
      '<img',
    );
  });
});

test.each([1.5, true, '1', null])('a heading offset of %s is refused', (offset) => {
  expect(() => parseMarkdownToHtmlFragment('## A', { headingOffset: offset as number })).toThrow(
    new TypeError('heading_offset must be an integer'),
  );
});
