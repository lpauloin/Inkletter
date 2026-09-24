# Changelog

Newest first. [Semantic versioning](https://semver.org): a major bump
means a document, a theme file or a call that used to work no longer
does.

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
