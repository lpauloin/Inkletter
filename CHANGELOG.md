# Changelog

Newest first. [Semantic versioning](https://semver.org): a major bump
means a document, a theme file or a call that used to work no longer
does.

## 4.1.0 — 2026-10-30

### Added

- **The JavaScript package exports its tree and its visitor** — `ast`,
  `NodeVisitor`, `ScopeStack` — and the grammar of a domain written without
  its scheme (`BARE_DOMAIN`, `isBareDomain`, `isSpelledBy`), for an
  application that lays a document out its own way: an editing surface that
  reads the text exactly as the render reads it. The Python package already
  had them (`inkletter.ast`, `inkletter.visitors`); it changes only its
  version, the two being released together.

## 4.0.0 — 2026-10-30

### Added

- **A JavaScript package, `inkletter` on npm** (`js/`): the same rules, the
  same tree, the same visitors, module for module — the post and its count,
  the HTML fragment and the MJML come out of it character for character as
  they come out of Python, the responsive HTML compiled by MJML's own browser
  build. What holds them together: `scripts/parity.py` writes what Python
  answers for every document its suite renders and for those of
  `parity/documents.json` — `parity/linkedin.json`,
  `parity/html_fragment.json`, `parity/mjml.json` — and the JavaScript tests
  want the same characters; the CI checks both sides.
- **The post as a feed shows it.** `render_linkedin` (`renderLinkedin` in
  JavaScript) returns the post, what LinkedIn counts for it, its lines —
  each fragment saying what it is (text, a mention, a hashtag, a link),
  what the feed shows of it (a mention's name, an address as written, its
  letters decoded) and what it costs — and whether bold, italic or a
  heading were written that the feed will not show. `shown_text` reads it
  on one string. `parse_markdown_to_linkedin` is that render, refused over
  its ceiling.
- **An HTML fragment output.** `parse_markdown_to_html_fragment` renders
  a document as the inside of a page — paragraphs, headings, quotes,
  lists, tables, code, bold, italic, struck text and links — for a page
  that sets it among its own content: a note in a PDF report, a comment
  on a screen. No theme applies; the page styles it. It is safe to set
  inside a page that trusts nothing the author typed: every text is
  escaped, raw HTML (inline or block) is dropped, a link to anything but
  `http`, `https`, `mailto` or `tel` is written as its label, a mention is
  the name it shows, and an image is its alternative text — whatever
  renders the fragment fetches nothing. A line break the author typed
  stays one (`<br>`), as a post keeps it.

### Changed

- **The parser is markdown-it** (`markdown-it-py`) in place of mistune.
  It reads CommonMark more closely — 98 % of its examples, against 91 %
  — and has a twin in JavaScript, line for line the same rules: what
  Inkletter reads is now read the same way in a browser. What Inkletter
  reads beyond CommonMark keeps its meaning, written as markdown-it
  plugins, one module each in `inkletter.plugins`. A few documents read differently, each
  time as CommonMark says:
  - a heading or a list right under a quote, without a blank line, ends
    the quote (`> a` then `## b`): it used to be read inside it, or —
    for a list — before it;
  - an entity is read only whole, its `;` included: `&copy 2026` stays
    text, where it used to become `© 2026`;
  - a table written without its last pipes no longer opens on an empty
    column;
  - marks nested deep (`***~~a **b *c ~~d~~ c* b** a~~***`) are all read;
  - the blank lines after an indented code block are the author's, like
    after any other block, and a post writes them;
  - a NUL character is replaced with `U+FFFD`;
  - an empty document is an empty mail body, without an empty section.

  `ASTRenderer` is now `ASTBuilder`, which turns markdown-it's tree into
  Inkletter's (`read_markdown` returns the document as parsed, before any
  pass), and `create_markdown` returns the parser itself. The plugins live in
  `inkletter.plugins`, one module each: `inkletter.bare_domains` and
  `inkletter.link_attributes` are now `inkletter.plugins.bare_domains`
  and `inkletter.plugins.link_attributes`.
- **A list ends where its author stopped writing it.** A line written
  right after an item, without a marker and without indentation, used to
  join the item (CommonMark's lazy continuation: `- Étapes` then `Après`
  read as one item); it is now a block of its own, in every output — the
  mail and the fragment show the list, then a paragraph; the text and the
  post, the list, then the line. A line indented under an item is still
  the item. The blank lines after a list's last item are counted with
  what follows, like any other run (`inkletter.plugins.typed_lists`).
- **A post keeps blocks typed line after line, line after line.** Two
  blocks the author wrote without a blank line between them — a sentence
  then a list, a list then a list of another kind, a list then a quote —
  were laid out with one blank line between them, which the author never
  typed; the post now writes the blank lines that were typed, none
  included. The other outputs, documents, keep separating their blocks.

### Removed

- **mistune**, and with it `blank_lines_plugin`, `bare_url_plugin` and
  `bare_domain_plugin`: the blank lines are counted from where each block
  starts and ends, and the bare addresses — written in full or as a
  domain — are one rule, `bare_links_plugin`.

## 3.4.0 — 2026-10-11

### Added

- **A domain written without its scheme is a link.** `exemple.com`,
  `app.exemple.fr/tarifs?x=1` and `www.exemple.museum` are read as links
  to `https://` plus what was written, in every output: a feed and a mail
  reader make them clickable anyway, so the URL factory is now offered
  them — a shortener shortens them, a counter charges them — like an
  address written in full. The label stays what the author wrote: the
  mail shows `exemple.com` on an anchor to `https://exemple.com`; the
  post and the plain text, which show addresses, write the address once.

  Two spellings are read: a name opening on `www.`, whatever its ending,
  and a name ending on one of a closed list of extensions
  (`inkletter.bare_domains.EXTENSIONS`: `com net org info biz io
  co ai app dev tech fr eu be ch lu ca uk de es it nl pt us`). The
  extension is in lower case — `fini.De retour` is a forgotten space, not
  a German site — and must end the name: `exemple.community` and
  `exemple.com.zip` are text. So are `readme.md`, a mail address, an
  accented name and a name inside a path. What follows the name — port,
  path, query, fragment — ends like any bare address, and never on the
  `?` or `!` of the sentence around it.

### Changed

- **A link labelled with a domain is written once** in a post:
  `[exemple.com](https://exemple.com/tarifs)` gives the address alone,
  as `[https://exemple.com](…)` already did, instead of
  `exemple.com : https://exemple.com/tarifs`.

## 3.3.0 — 2026-09-24

### Changed

- **The dependencies are declared as ranges**, not as exact pins:
  `click>=8.1,<9`, `mistune>=3.3.4,<4`, `mjml-python>=1.4,<2` and
  `tomli>=2.0` under Python 3.10. A pin in a library's metadata makes it
  unresolvable beside any other package that pins the same name
  differently; a range resolves as before — `uv.lock` is unchanged — and
  leaves the choice to whoever installs. The floors are tested: the suite
  passes with click 8.1.8 and with 8.5.0, on mistune 3.3.4 and
  mjml-python 1.4.0 as on 1.4.2. mistune stays at `>=3.3.4`: a malformed
  table fails on 3.3.0.

## 3.2.0 — 2026-09-24

### Changed

- **A post keeps the blank lines its author left.** A run of them
  separates two blocks by as many lines as were typed instead of folding
  into one: a document says nothing by a second blank line, a post does.
  The blank lines a document opens or ends on still separate nothing —
  the platform trims them before counting — and a list still reads the
  ones that follow it as its own. Only the LinkedIn output: the mail and
  the text alternative render exactly as before.

### Added

- **`BlankLine.lines`**, how many blank lines the run was. A visitor that
  does not read it renders as it did.

### Fixed

- **A stroke never touches an emoji through the space beside it.** The
  space between two struck words is struck as before; the one next to
  something the stroke skips is skipped too, and costs one unit less.

## 3.1.0 — 2026-09-13

### Changed

- **`Link` is abstract.** A tree holds `UrlLink`, `MailLink`, `TelLink`
  and `Mention`, chosen by the target's scheme (`ASTRenderer.LINKS_BY_SCHEME`);
  a `urn:` of any namespace is a mention. A visitor's `visit_Link` no
  longer runs: name `visit_UrlLink` and the other kinds it means.
  Documents, themes and the public calls are untouched.
- **A bare address is a link in every output**, and the `autolink`
  parameter of `parse_markdown_to_ast` is gone. An email links it, a URL
  factory shortens it, one alone in bold is a button.

### Added

- **`Hashtag(name)`**, a node read at parse time: `#équipe_rh` is one tag,
  never an italic. `#2026` and `C#` are text; `# heading` is a heading.
  Written as is everywhere; an email may colour it (`[hashtags] color`).
- **`Link.scheme`, `Image.scheme`, `ImageLink.scheme`**, read with
  `urllib.parse`; `MailLink.address`, `TelLink.number`.
- **`styles` on every text and code span**: the styles in force around
  it, set by the annotation. The label of a lone bold link carries none.

### Fixed

- **Bold and italic together** take the bold italic look-alikes, in any
  nesting; strikethrough adds its stroke on top.
- **A hashtag is never substituted**: `**#marketing**` stays `#marketing`.
- **A lone bold link keeps its own letters**: on a feed a call to action
  is a line of text.
- **Strikethrough leaves an emoji whole.**
- **A feed writes `mailto:` and `tel:` as the address and the number**,
  and `<bonjour@exemple.fr>` once rather than twice.
- **A bare address** never ends on `*`, `_` or `~`, and keeps a final `)`
  only when it closes one of its own — `**https://exemple.fr**` is bold,
  `(see http://a.fr/b)` keeps the sentence's parenthesis.

## 3.0.0 — 2026-09-10

### Changed

- **`URLFactory.rewrite_link` takes `is_button` and `is_bold`** — what
  the document says about the link: the button (a lone bold link, where
  buttons exist), and bold text around it (how an output without
  buttons, the LinkedIn one, still tells the call to action apart). A
  factory written against 2.x with `def rewrite_link(self, url)` no
  longer works: add the parameters. `rewrite_image` is unchanged. This is the major bump, and the reason for it — the one
  thing the document says about a link that a factory may want to know
  now travels with the URL, rather than through a second method or a
  result to read back.
- The URL rewrite now runs last, after the annotation pass, so that a
  button is one by the time its URL is offered.
- The line machinery weighs what it lays out: `TextElement` may carry
  a `cost`, `Indent` may carry any prefix (a quote's `> ` is one), and
  `CodeBlockResolver(measure=…)` sums each line in the caller's unit as
  it resolves — `length` beside the text. The LinkedIn output is the
  plain-text one with a feed's choices and a price on every fragment.
- A trimming pass right after parsing: a break inside a link's label, a
  mention's name or a table cell becomes a space, and the whitespace at
  either end goes. No output rendered them otherwise; the tree now says
  so itself.

### Added

- **A LinkedIn output**: `parse_markdown_to_linkedin(markdown)` renders
  the same document as a post and returns its text. See the README for
  the three choices it makes (mentions, formatting, counting) and for
  why a first comment is a second document rather than a section of
  this one. Images are not supported there: one written in the document
  is left as written.
- `LengthError`, raised when the rendered post is over `max_length`
  (4000 by default, the transport limit). Nothing is ever truncated: a
  post cut mid-sentence without warning is worse than one that refuses
  to leave. It carries the length counted and the limit.
- `URLFactory.link_length`, the width of the links a factory produces
  when it is fixed. The LinkedIn output prices every link at it, so a
  post is counted for what will be published before the short links
  exist.
- `inkletter.counting`, holding the unit the platform counts in — UTF-16
  code units —, that ceiling, and what each kind of fragment costs:
  ordinary text weighs what it says, a mention weighs the name it
  displays rather than the marker carrying it, and a link weighs the
  short link it will become. The text is NFC-normalized first: a
  decomposed accent counts as two units on the platform and shows as one
  letter.

### Fixed

- A URL factory is no longer handed targets that name something rather
  than locating it — `mailto:`, `tel:`, and the `urn:` of a mention,
  which a shortener would have turned into a dead link. A path without
  a scheme, such as a local image, still reaches the factory.

## 2.2.0 — 2026-08-08

### Changed

- A percentage is no longer accepted as an image dimension. `mj-image`
  sizes in pixels, so `{width=50%}` passed validation and was then
  dropped, rendering at the full column width — the shape of error this
  syntax exists to avoid. A document using it now fails loudly instead,
  which is why this is not a major bump: nothing that worked stopped
  working, a wrong render became a refusal.

### Fixed

- **A width was ignored on a phone.** `fluid-on-mobile` was set on every
  image, and its whole purpose is to go full width *even though a width
  is set* — so a 72px logo arrived at the full column width on the
  screens that carry most opens. Measured, an image without a width
  renders the same with or without it: the attribute only ever undoes a
  width, so it is now set only under `--no-link-attributes`, where no
  image can carry one and such a document keeps its output byte for
  byte.

## 2.1.0 — 2026-08-08

### Fixed

- **A web font whose family needs quotes never applied.** The stack was
  normalised by stripping its quotes so the `mj-font` name would match,
  which works until a family name is not a valid CSS identifier — a
  digit is enough. Measured in Chrome: `font-family: Source Sans 3,
  Helvetica, sans-serif` is dropped whole and the reader gets *Times*,
  not even the next font in the stack. The stack is now left exactly as
  written, and the `mj-font` is declared with the spelling the stack
  uses, so the two agree without either being rewritten.

  `Theme.fonts` consequently reports each name as the stack spells it —
  `("'lora'", url)` for a stack of `'lora', Georgia` — rather than
  unquoted.

## 2.0.0 — 2026-08-07

A year of work that was never installable. `1.1.0` was a version number
in `pyproject.toml`, never published, and is folded in here.

### Breaking

- Heading sizes moved into a subsection per level: `[headings] h1_size`
  is now `[headings.h1] size`. An old theme file fails loudly.
- `use_style` and `render_mjml` are gone. Styling comes from the theme,
  and there is nothing left to mask.

### Added

- **Plain-text output** — `parse_markdown_to_text`, `inkletter md2txt`:
  the other half of a multipart email, with underlined headings and
  ASCII-aligned tables.
- **Image attributes** — `![Acme](logo@2x.png){width=96px align=left}`,
  Pandoc's `link_attributes` narrowed to `px` and `%`.
- **Web fonts** — a `[fonts]` table, emitted as `mj-font`. A font the
  text never uses is refused rather than silently not loading.
- **Document title** — an opening plain-text `# heading` becomes the
  email's `<title>`.
- **Heading alignment per level** — `[headings.h1] align = "center"`,
  carried as an `mj-text` attribute so it survives clients that drop the
  `<style>` block. `h4` to `h6` are sized too.
- **`escape_markdown`** — for values substituted into a Markdown source
  before conversion, where `[Click here](https://evil.tld)` would
  otherwise become a working link in the mail you send.
- **URL factories** — rewrite or shorten every link and image source,
  with a Bitly implementation included.
- **Image layout** — a paragraph of images becomes a row of columns; an
  image opening or closing a paragraph becomes an image beside its text.
- **Buttons** — a paragraph holding nothing but a bold link.
- **Themes** — seven presets, a TOML theme file, `--theme`.
- Raw HTML passed through untouched, a public API, CI, and `black`.

### Changed

- **The Django integration is an order, not a feature**: resolve the
  template while the document is still Markdown, then convert. Loops
  over table rows, filters with a `|` in a cell and conditionals around
  anything then work with no support of any kind. See
  [sample/DJANGO.md](sample/DJANGO.md).
- **All styling lives in the theme**, applied by one annotation pass;
  the code generator never sees a theme.
- **Jinja2 is no longer a dependency** — three placeholders never needed
  a templating engine. Runtime dependencies: `click`, `mistune`,
  `mjml-python`.
- Every alignment a theme can set is validated, `[buttons]` and
  `[images]` included.
- Python 3.10 minimum; click 8.4, mistune 3.3, mjml-python 1.4.

### Fixed

- Paragraphs inside a quote or a list item ran together in HTML while
  the text half separated them — the same email saying two things.
- A hand-written `<a href>` lost its URL in the text half.
- A quoted font family never loaded: MJML matches `mj-font` literally,
  so `"Lora"` left the file in the head and the font unused — while the
  validation, comparing unquoted names, said it was fine.
- `mj-image` leaked into `mj-text` for images caught in inline
  formatting.
- Table text ignored the theme typography.
- Mixed task and normal lists, the start number of ordered lists, image
  alt text containing formatting, HTML escaping in text and attributes.

## 1.0.0 — 2025-08-11

Markdown to MJML to responsive HTML, with a browser preview.

## 0.1.1 — 2025-06-21

Packaging fixes, working template preview.

## 0.1.0 — 2025-06-20

Initial release.
