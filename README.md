# Inkletter

[![GitHub Repo](https://img.shields.io/badge/GitHub-Inkletter-blue?logo=github)](https://github.com/lpauloin/Inkletter)
[![CI](https://github.com/lpauloin/Inkletter/actions/workflows/ci.yml/badge.svg)](https://github.com/lpauloin/Inkletter/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/inkletter.svg)](https://badge.fury.io/py/inkletter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Write your emails like prose, send them like a pro.**

Inkletter turns plain Markdown files into beautiful, responsive MJML and HTML email
layouts, ready to be previewed, shared or sent to the world.

## Why Inkletter?

Because writing HTML emails by hand is like ironing socks: pointless and painful.

With Inkletter, you write your content in **Markdown** (like a decent human being),
and it becomes a **gorgeous, mobile-friendly HTML email** powered by MJML.

## Features

- Markdown to MJML or to final responsive HTML, in one command
- Seven built-in themes, or your own theme in a small TOML file
- Live preview in your browser, with a device simulator (iPhone, iPad, desktop)
- Clean Python API if you'd rather script it
- Runs entirely on your machine, no account, no vendor lock-in

## Installation

Python 3.10+ required.

```bash
pip install inkletter
```

Or for development:

```bash
git clone https://github.com/lpauloin/Inkletter.git
cd Inkletter
pip install -e .
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

## Theming

Every command accepts `--theme` with a built-in preset or a TOML file:

```bash
inkletter preview newsletter.md --theme dark
inkletter md2html newsletter.md --theme mytheme.toml -o out.html
inkletter md2mjml newsletter.md --no-theme   # bare MJML, no styling
```

The built-in presets, rendered on desktop and mobile:

![The built-in themes](sample/themes.png)

### Theme files

A theme file is partial — set only what you want to change:

```toml
[layout]
width = "640px"

[text]
font_family = "Georgia, serif"

[links]
color = "#c0392b"
underline = false
```

| Section | Keys |
|---------|------|
| `[layout]` | `width`, `background_color`, `content_background_color`, `section_padding` |
| `[text]` | `font_family`, `font_size`, `line_height`, `color` |
| `[headings]` | `font_family`, `color`, `font_weight`, `h1_size`, `h2_size`, `h3_size` |
| `[links]` | `color`, `underline` |
| `[code]` | `font_family`, `background_color`, `color` |
| `[quote]` | `color`, `border_color`, `font_style` |
| `[divider]` | `color`, `width` |
| `[table]` | `border_color`, `cell_padding`, `header_color`, `header_background_color` |

Any unknown section or key fails loudly, with the list of valid ones.

### From Python

Same defaults, same presets, plus optional named color palettes:

```python
from inkletter.colors import Blue
from inkletter.md_to_html import parse_markdown_to_html
from inkletter.theme import Links, Text, Theme

theme = Theme(text=Text(font_family="Georgia, serif"), links=Links(color=Blue.DARK))
html = parse_markdown_to_html(markdown, theme=theme)
```

## Samples

- [sample.md](sample/sample.md) — the Markdown source
- [sample.html](sample/sample.html) — the generated responsive email
- [sample/themes/](sample/themes/) — the same source rendered with every preset

## Contributing

French or not, you are welcome to contribute.
Fork it, branch it, test it, PR it — with love.

```bash
pip install -r requirements-test.txt
pytest
```

Every push and pull request runs through the GitHub Actions CI on Python 3.10 to 3.13.

## License

MIT — but don't forget to say "merci" 😉

Made with ❤️ and `markdown` in France.
