// The responsive email, compiled by MJML's own browser build: its HTML is
// not MRML's, the Python package's, so it is read for what it shows.

import { expect, test } from 'vitest';
import { parseMarkdownToHtml, Theme, THEMES } from '../src/index.js';

test('the MJML compiles into a mail that shows the document', async () => {
  const html = await parseMarkdownToHtml('# Bonjour\n\nUn **mot** et [un lien](https://exemple.fr).');
  expect(html).toMatch(/^<!doctype html>/i);
  expect(html).toContain('<h1');
  expect(html).toContain('<strong>mot</strong>');
  expect(html).toContain('href="https://exemple.fr"');
});

test.each(Object.keys(THEMES))('the %s theme compiles a mail with a button', async (name) => {
  const html = await parseMarkdownToHtml('# Titre\n\n**[Réserver](https://exemple.fr)**', { theme: Theme.named(name) });
  expect(html).toContain('href="https://exemple.fr"');
});

test("only a font's quotes are rewritten for the compiler, never the author's code", async () => {
  const html = await parseMarkdownToHtml(
    'Search [our directory](https://e.com/search?name=) and set `lang="fr"` in the form.\n\n' +
      '```html\n<div class="x">hi</div>\n```\n\n![logo](https://e.com/l.png)',
    { theme: Theme.named('green') },
  );
  expect(html).toContain('lang=&quot;fr&quot;');
  expect(html).toContain('class=&quot;x&quot;');
});
