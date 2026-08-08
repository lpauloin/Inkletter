# Changelog

Newest first. [Semantic versioning](https://semver.org): a major bump
means a document, a theme file or a call that used to work no longer
does.

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
