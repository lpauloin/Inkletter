// The responsive email, compiled by MJML's own browser build: its HTML is
// not MRML's, the Python package's, so it is read for what it shows.

import { expect, test } from 'vitest';
import { parseMarkdownToHtml } from '../src/index.js';

test('the MJML compiles into a mail that shows the document', async () => {
  const html = await parseMarkdownToHtml('# Bonjour\n\nUn **mot** et [un lien](https://exemple.fr).');
  expect(html).toMatch(/^<!doctype html>/i);
  expect(html).toContain('<h1');
  expect(html).toContain('<strong>mot</strong>');
  expect(html).toContain('href="https://exemple.fr"');
});
