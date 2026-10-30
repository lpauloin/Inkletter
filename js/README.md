# inkletter

Markdown to LinkedIn posts, HTML fragments, MJML and responsive emails — the
JavaScript twin of the [Python package](https://github.com/lpauloin/Inkletter),
output for output: the post, its count and its lines, the fragment and the
MJML come out character for character as they come out of Python.

```bash
npm install inkletter
```

```js
import { parseMarkdownToHtmlFragment, parseMarkdownToMjml, renderLinkedin, Theme } from 'inkletter';

const render = renderLinkedin('Merci à [Acme](urn:li:organization:12345678) !');
render.text; // 'Merci à @[urn:li:organization:12345678|Acme] !'
render.length; // 14
render.shownText; // 'Merci à Acme !'
parseMarkdownToHtmlFragment('Un *mot*.'); // '<p>Un <em>mot</em>.</p>'
parseMarkdownToMjml('# Bonjour', { theme: Theme.fromDict({ links: { color: '#0a66c2' } }) });
```

- `renderLinkedin(markdown, { unicodeStyling, urlFactory })` — the post, what
  LinkedIn counts for it, its `lines` (each segment's kind, what the feed
  shows of it, what it costs), `shownText`, and `unrenderedFormatting` /
  `unrenderedHeadings`; `parseMarkdownToLinkedin` refuses a post over
  `maxLength` (4000 by default) with a `LengthError`.
- `parseMarkdownToHtmlFragment(markdown, options)` — the inside of a page,
  safe to set in one that trusts nothing the author typed.
- `parseMarkdownToMjml(markdown, { theme, … })` — the email as MJML.
- `await parseMarkdownToHtml(markdown, options)` — the responsive email,
  compiled by MJML's browser build: install `mjml-browser` and `cheerio`
  beside this package. Loaded only when called.

The Python package's README documents the Markdown it reads and every choice
each output makes.
