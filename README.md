# Inkletter

[![GitHub Repo](https://img.shields.io/badge/GitHub-Inkletter-blue?logo=github)](https://github.com/lpauloin/Inkletter)
[![CI](https://github.com/lpauloin/Inkletter/actions/workflows/ci.yml/badge.svg)](https://github.com/lpauloin/Inkletter/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/inkletter.svg)](https://badge.fury.io/py/inkletter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Inkletter — write your newsletter in Markdown, get a responsive themeable HTML email](sample/banner.png)

**Write your emails like prose, send them like a pro.**

Inkletter turns plain Markdown files into beautiful, responsive MJML and HTML email
layouts, ready to be previewed, shared or sent to the world.

## Why Inkletter?

Because writing HTML emails by hand is like ironing socks: pointless and painful.

With Inkletter, you write your content in **Markdown** (like a decent human being),
and it becomes a **gorgeous, mobile-friendly HTML email** powered by MJML.

## Features

- Markdown to MJML or to final responsive HTML, in one command
- The same Markdown rendered as a LinkedIn post — mentions, short-link
  aware counting, and a refusal rather than a truncation
- Layout from plain Markdown structure: side-by-side image rows, image-beside-text
  media objects, and call-to-action buttons from a lone bold link
- Seven built-in themes, or your own theme in a small TOML file
- Image sizing with Pandoc's `{width=96px}` attributes
- Drops into a Django app: render the Markdown, then convert it
- Live preview in your browser, with a device simulator (iPhone, iPad, desktop)
- Clean Python API if you'd rather script it
- Runs entirely on your machine, no account, no vendor lock-in

## Installation

Python 3.10+ required.

```bash
pip install inkletter
```

See the [changelog](CHANGELOG.md) for what each version changed.

Or for development:

```bash
git clone https://github.com/lpauloin/Inkletter.git
cd Inkletter
uv sync
```

## Usage

### Preview a Markdown file as a responsive email

```bash
inkletter preview newsletter.md
```

Opens a split view in your browser: your Markdown, the generated MJML, and the
rendered email in a device simulator.

### Convert to HTML

```bash
inkletter md2html newsletter.md -o newsletter.html --view
```

Writes the final email HTML, and opens it in your browser with `--view`.

### Export the raw MJML

```bash
inkletter md2mjml newsletter.md -o newsletter.mjml
```

Without `-o`, the MJML is printed to stdout, ready to be piped anywhere.

### Plain-text version

```bash
inkletter md2txt newsletter.md -o newsletter.txt
```

The plain-text alternative for `multipart/alternative` sending — better
deliverability, and a readable email everywhere. Headings are underlined,
links become `label <url>`, buttons become `→ label : url` call-to-action
lines, and tables are ASCII-aligned.

## LinkedIn posts

The same Markdown, rendered as a post — a feed has no rich formatting, so
a post is text, and everything else is what a feed does differently:

```python
from inkletter import parse_markdown_to_linkedin

text = parse_markdown_to_linkedin(markdown, url_factory=my_shortener)
```

One document in, one string out. Nothing is invented on top of
CommonMark:

| In the Markdown          | In the post                                   |
|--------------------------|-----------------------------------------------|
| a link                   | `label : https://…` — no angle brackets       |
| a bare address           | itself, once: it is a link like any other     |
| `# heading`              | its text on its own line, no underline        |
| `- item`                 | `• item`, since list markup is refused        |
| `1. item`                | its number, as written                        |
| a bold link on its own   | `label : url` — a feed draws no button; the   |
|                          | factory is told it was bold                   |
| a table                  | one line per row, cells joined by `—`         |
| `---`                    | a blank line: a feed draws no rule            |
| `**bold**` `*italic*`    | the words alone (see below)                   |
| an image                 | left exactly as written — not supported       |

### Three choices, so you know what to expect

**A mention is a link whose target is the URN**, which is the only thing
that identifies an entity — a name alone mentions nobody:

```markdown
Merci à [Acme](urn:li:organization:12345678) !
```

It goes out as `@[urn:li:organization:12345678|Acme]`, the form a
publishing API resolves into a real, blue, clickable mention. That is the
single form Inkletter emits: LinkedIn's own read-back notation
`@[Name](urn:…)` is *not* it — written into a post it goes inert and makes
the rest of the text escape itself. A name is passed through untouched,
because the match is exact and case-sensitive. A name containing `|` or
`]` cannot be expressed — they delimit the marker and nothing escapes them
— so that one goes out as `@Name`, plain text.

**Formatting is removed, not faked** — unless you ask. The platform has no
bold, italic or strikethrough, so by default the words go out plain.
`unicode_styling=True` substitutes mathematical look-alikes instead. They
are text, not formatting: a screen reader spells them out letter by
letter, the platform's search does not match them, and each letter costs
two characters rather than one. Hence opt-in. A mention or an address
inside a styled run is never substituted, or it would stop resolving.

**Length is counted the way the platform counts it**, in UTF-16 code
units — an emoji costs 2, a skin tone 4, a Unicode bold letter 2 — on a
text whose accents are composed first (the platform counts a decomposed
`é` as two and shows one), declared fragment by fragment as the document
is written rather than measured on the finished string: only the render
knows that a mention weighs the name it displays instead of the marker
carrying it. A URL factory that sets `link_length` prices every link at
that width instead of at the address written in the document — your
shortener produces links of one fixed size, and they do not exist yet
when the text is counted.

Over the ceiling, nothing is truncated — `parse_markdown_to_linkedin`
raises `LengthError`, which carries the length it counted and the limit,
since a post cut mid-sentence without warning is worse than one that
refuses to leave. The default is 4000, the transport limit; pass your own
`max_length=`, or `max_length=None` to never refuse.

### A first comment is a second document

Write it in its own file, render it with a second call, and publish it
where it belongs. Inkletter has no notion of a first comment: it renders
one document into one text, and a `---` in your source stays a horizontal
rule rather than quietly deciding what gets published.

```python
comment = parse_markdown_to_linkedin(footnotes, max_length=1250)
```

## Django templates

Building emails for a Django app? Let Django resolve the template while
the document is still Markdown, then convert what comes out:

```python
from django.template import Context
from django.template.loader import get_template

from inkletter import parse_markdown_to_html, parse_markdown_to_text

# autoescape off: this render produces Markdown, not HTML
markdown = get_template("emails/welcome.md").template.render(Context(context, autoescape=False))

html = parse_markdown_to_html(markdown)
text = parse_markdown_to_text(markdown)
```

In that order everything works with no special support: loops over
table rows, filters with a `|` in a cell, conditionals around anything.
The converter only ever sees plain Markdown, and the text part can align
its table columns on the real values.

Values that are not yours need escaping — in a Markdown document,
`[Click here](https://evil.tld)` is a working link, and a server
response holding ` ``` ` escapes the code block you put it in.
`escape_markdown` ships for the first; the second is `textwrap.indent`.
Wiring them to template filters is three lines in your own app:

```python
from inkletter import escape_markdown

register.filter("md", escape_markdown)
register.filter("md_code", lambda value: textwrap.indent(str(value), "    "))
```

See the **[Django integration guide](sample/DJANGO.md)** for the setup,
the full send function, and why this order.

## Sizing an image

A logo exported at 2x arrives twice too large unless the document says
how wide to draw it — and no theme can say it, because the theme does
not know which image you inserted. Put the facts in braces, Pandoc's
`link_attributes` syntax:

```markdown
![Acme](logo@2x.png){width=96px}

![Screenshot](shot.png){width=320px align=left}

[![Acme](logo@2x.png)](https://acme.example){width=96px}
```

`width`, `height` and `align` — and nothing else. A dimension is a fact
about the asset; an appearance is a choice of theme, so no CSS property
is ever accepted here. Lengths are in `px`, a bare number means pixels,
and alignment is `left`, `center` or `right`.

A width holds on a phone too — an image without one follows its column
either way, so nothing is made responsive by ignoring it.

A block only counts when it is glued to an image, or to a link wrapping
one. A space before the brace keeps it as text, and so does anything
that is not an attribute — `{beta}` or `{see below}` travel through
untouched. Turn the whole thing off with `--no-link-attributes`.

### Document title

When your Markdown opens with a plain-text `# heading`, it becomes the
email's `<title>` — the tab of a "view in browser" page, and what a
screen reader announces. A heading carrying emphasis, a link or an image
is left alone rather than flattened, and the document simply has no
title. This is not the subject line: that one you pass when sending.

## Layout

Layout is driven by plain CommonMark structure — no custom syntax, the same
file stays clean in any Markdown editor (and reusable for other channels):

- A paragraph made **only of images** becomes a row of side-by-side columns
  (up to 4 on one row, more wrap into rows of 3):

  ```markdown
  ![Left view](left.png) ![Right view](right.png)
  ```

- A paragraph **starting (or ending) with a single image** beside text becomes
  a media object — image next to its text, 30/70 by default. Put the image
  last to place it on the right:

  ```markdown
  ![Portrait](jean.png) Jean joined the team this week.
  He will own the rendering platform.
  ```

- A paragraph made **only of a bold link** becomes a call-to-action button
  (a real `mj-button`, styled by the theme). A plain link stays a link, and
  bold links inside lists, tables or quotes stay bold links:

  ```markdown
  **[Get started](https://example.com/go)**
  ```

  Pass `--no-bold-link-button` to keep bold links as links.

On mobile everything stacks gracefully, image on top. Ratios, spacing and
colors are tuned in the `[images]` and `[buttons]` theme sections below —
including `text_layout = "stacked"` to disable media-object columns entirely.

## Theming

There is always a theme: without `--theme`, the default one applies.
Every command accepts `--theme` with a preset name or a theme file:

```bash
inkletter md2html newsletter.md --theme dark
inkletter md2html newsletter.md --theme mytheme.toml
```

### Built-in presets

| Preset    | Mood                                                           |
|-----------|----------------------------------------------------------------|
| `default` | Clean and neutral — Helvetica, gray text, blue links           |
| `dark`    | Slate night mode — light text, Trebuchet MS headings           |
| `crystal` | Airy and elegant — Palatino headings, cold blue accents        |
| `blue`    | Corporate and trustworthy — Tahoma text, Trebuchet MS headings |
| `green`   | Organic and editorial — Georgia throughout                     |
| `red`     | Bold and editorial — Georgia headings over Helvetica text      |
| `yellow`  | Warm and friendly — Verdana text, Trebuchet MS headings        |

Each preset is rendered on desktop and on a 375px mobile screen in the
**[theme gallery](sample/THEMES.md)**.

### Write your own

A theme file is partial — set only what you want to change,
everything else keeps the default look:

```toml
[layout]
width = "640px"

[text]
font_family = "Georgia, serif"

[links]
color = "#c0392b"
underline = false
```

| Section      | Keys                                                                                                     |
|--------------|----------------------------------------------------------------------------------------------------------|
| `[layout]`   | `width`, `background_color`, `content_background_color`, `section_padding`                               |
| `[text]`     | `font_family`, `font_size`, `line_height`, `color`                                                       |
| `[headings]` | `font_family`, `color`, `font_weight`, and one `[headings.hN]` subsection per level (`size`, `align`)   |
| `[links]`    | `color`, `underline`                                                                                     |
| `[code]`     | `font_family`, `background_color`, `color`                                                               |
| `[quote]`    | `color`, `border_color`, `font_style`                                                                    |
| `[divider]`  | `color`, `width`                                                                                         |
| `[table]`    | `border_color`, `cell_padding`, `header_color`, `header_background_color`                                |
| `[images]`   | `align`, `row_gap`, `border_radius`, `text_layout`, `media_ratio`                                        |
| `[buttons]`  | `background_color` (inherits `links.color`), `color`, `border_radius`, `font_weight`, `padding`, `align` |

Each heading level is its own subsection, so a centred headline over
left-aligned subheadings — the shape most newsletters take — is two
lines:

```toml
[headings.h1]
align = "center"
```

Only what you name changes: `h1` keeps its default size, and `h2` to
`h6` keep everything. Any unknown section or key fails loudly, with the
list of valid ones.

### Web fonts

A `[fonts]` section loads a font your readers may not have. Declare the
name and a stylesheet URL, then use it in `text.font_family`:

```toml
[fonts]
Lora = "https://fonts.googleapis.com/css2?family=Lora"

[text]
font_family = "Lora, Georgia, serif"
```

**The fallback is the main rendering, not a safety net.** Web fonts load
in Apple Mail, iOS Mail, Outlook for Mac and Thunderbird. Gmail, Outlook
for Windows and most webmails ignore them and show the next font in the
stack — so `Lora, Georgia, serif` has to look good *without* Lora.

MJML only loads a font that a component actually uses, and
`text.font_family` is the only theme setting it reads. A font declared
for the headings alone would never load, so Inkletter refuses that
theme rather than letting it fail in silence. Without a `[fonts]`
section, an Inkletter email makes no external request at all.

### From Python

Same defaults, same presets, plus optional named color palettes:

```python
from inkletter.colors import Blue
from inkletter.md_to_html import parse_markdown_to_html
from inkletter.theme import Links, Text, Theme

theme = Theme(text=Text(font_family="Georgia, serif"), links=Links(color=Blue.DARK))
html = parse_markdown_to_html(markdown, theme=theme)
```

## URL shortening

Every URL of the document can go through a factory you define — the
classic newsletter needs: shorteners, click tracking, UTM tags. A Bitly
implementation ships with Inkletter:

```python
from inkletter.md_to_html import parse_markdown_to_html
from inkletter.shortener import BitlyShortener

html = parse_markdown_to_html(markdown, url_factory=BitlyShortener(token="..."))
```

Or write your own: subclass `URLFactory` and override only what concerns
you — `rewrite_link` for click URLs (links, image links, buttons),
`rewrite_image` for image sources. `rewrite_link` also receives what
the document says about the link: `is_button` for the one that is a
button — a lone bold link, the call to action — and `is_bold` for a
link inside bold text; a shortener that does not care ignores both. A shortener
that only overrides `rewrite_link` never touches images, by simple
inheritance:

```python
from inkletter.shortener import URLFactory


class UTMTagger(URLFactory):
    def rewrite_link(self, url, is_button=False, is_bold=False):
        medium = "cta" if is_button else "email"
        return f"{url}?utm_source=newsletter&utm_medium={medium}"
```

A factory whose links are all the same width can say so, and the LinkedIn
output will count every link at that width rather than at the address the
document carries:

```python
class MyShortener(URLFactory):
    link_length = len("https://exa.mp/r/abc123")
```

`BitlyShortener` shortens each distinct URL once (in-memory cache), and
exceptions raised by a factory propagate untouched. Python API only —
the CLI does not expose factories.

A factory is only ever handed an address: a target that *names* something
rather than locating it — an entity URN, a `mailto:`, a `tel:` — never
reaches it, because rewriting one destroys it. A path with no scheme at
all is an address like any other, so a local image still goes through.

## Samples

- [sample.md](sample/sample.md) — the Markdown source
- [sample.html](sample/sample.html) — the generated responsive email
- [sample/themes/](sample/themes/) — the same source rendered with every preset
- [theme gallery](sample/THEMES.md) — all presets at a glance, desktop and mobile

## Contributing

French or not, you are welcome to contribute.
Fork it, branch it, test it, PR it — with love.

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Those are the three the CI runs, in that order, on Python 3.10 to 3.13 —
every push and every pull request. Run them as written rather than an
equivalent: a command of your own has a different scope.

## License

MIT — but don't forget to say "merci" 😉

Made with ❤️ and `markdown` in France.
