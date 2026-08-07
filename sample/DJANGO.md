# Using Inkletter in a Django app

Inkletter knows nothing about Django, and does not need to. The
integration is an **order**: Django resolves the template while the
document is still Markdown, then Inkletter converts what comes out.

```
Markdown + tags  →  Django  →  plain Markdown  →  Inkletter  →  HTML + text
```

Everything the data decides is settled before the converter runs, so it
only ever sees plain Markdown. That is what makes loops, conditionals
and filters work with no special support at all.

## Setup

Two lines of glue, in your own app — `yourapp/templatetags/markdown.py`:

```python
import textwrap

from django import template

from inkletter import escape_markdown

register = template.Library()
register.filter("md", escape_markdown)
register.filter("md_code", lambda value: textwrap.indent(str(value), "    "))
```

Inkletter ships the escaping, not the plumbing: it has no idea Django
exists and never imports it. The rule it implements is CommonMark's —
any ASCII punctuation may be backslash-escaped — and the code-block half
is `textwrap.indent` from the standard library. Nothing to keep in sync.

## Sending

```python
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template

from inkletter import parse_markdown_to_html, parse_markdown_to_text


def send_markdown_email(template_name, context, subject, to):
    """Resolve a Markdown template, convert it, send both parts."""
    # autoescape off: this render produces *Markdown*, not HTML, so
    # escaping for HTML here would put &amp; in front of your reader.
    # Escaping belongs on the values — that is what |md is for.
    markdown = get_template(template_name).template.render(
        Context(context, autoescape=False)
    )

    message = EmailMultiAlternatives(
        subject, parse_markdown_to_text(markdown), to=to
    )
    message.attach_alternative(parse_markdown_to_html(markdown), "text/html")
    message.send()
```

Pass a `theme=` to either converter if you do not want the default one.

`get_template(...).template.render(...)` goes through Django's loader
cache. Reading `.template.source` and building a `Template` yourself
short-circuits it and recompiles on every send — measured 5× slower, for
strictly the same output, `{% include %}` included.

## Escape everything that is not yours

**This is a security control, not a cosmetic one.** A value now lands in
a **Markdown** document, and Markdown makes links. Without escaping, a
value of `[Click here](https://evil.tld)` becomes a *working, clickable
link in the mail you send*, and well-formed HTML passes through
verbatim. Django's own escaping guards HTML and stops neither.

Two filters, because escaping is not the same job in the two places a
value can land.

### `|md` — a value in the flow of the text

```django
{% load markdown %}

Hi {{ member.first_name|default:'there'|md }},

Your folder {{ folder.name|md }} keeps files for {{ folder.days|md }}.
```

It backslash-escapes every ASCII punctuation character — CommonMark's
own definition, not a guessed list. The backslashes are markup, so they
disappear when the Markdown is parsed and no reader ever sees them.

Put it **last** in a chain, so it escapes whatever the filters before it
produced. Your own words — the ones you wrote in the template — need no
filter. Only the data does.

### `|md_code` — a value as a code block

This is where the least trustworthy data goes: a server response, an
error message, a filename someone else chose. **Do not put it in a
fenced block.**

```django
Here is what the server said:

{{ response|md_code }}
```

Four spaces on every line make an *indented* code block. Two reasons a
fence will not do, both of them measured:

- **`|md` is unusable inside a fence.** Its backslashes are not markup
  there, they are content, so the reader gets
  `erreur\: champ manquant`.
- **A fence can be escaped.** The block is closed by a delimiter, and a
  value containing ` ``` ` ends it early — everything after it is then
  parsed as Markdown, bold text and clickable links included. An
  indented block has no closing delimiter: indentation is the only thing
  keeping it open, and a line of the value cannot take it away.

Leave a blank line before the tag and put it at the start of its line;
the filter supplies the four spaces, including on the first line.
`textwrap.indent` leaves blank lines alone, which is what an indented
block wants — a blank line inside one does not end it.

## A complete example

```django
{% load markdown %}# Storage limits are changing

Hi {{ member.first_name|default:'there'|md }},

| Folder | Keeps for |
|---|---|
{% for f in folders %}| {{ f.name|md }} | {{ f.days|default:"no limit"|md }} |
{% endfor %}

In **{{ grace_days }} days** those folders revert.

{% if last_error %}
The last sync reported:

{{ last_error|md_code }}
{% endif %}

{% if paid %}
Thanks for being on a paid plan.
{% else %}
**[See the plans]({% url 'plans' %})**
{% endif %}
```

The HTML part gets a themed table with one row per folder. The text part
gets the same table, its columns aligned on the **real values**:

```
Folder                   | Keeps for
-------------------------+----------
Invoices                 | 90 days
Contracts                | no limit
Scanned receipts archive | 365 days
```

That alignment is the clearest sign the order is right: it can only be
computed once the data is there.

## Why this order and not the other one

Converting first and leaving the tags in the output would give you a
pair of Django templates you could commit — but the tags would then have
to survive Markdown, MJML and an XML compiler, and they do not survive
intact:

- a `{% for %}` on its own line **ends** a Markdown table instead of
  repeating its rows;
- a filter's `|` **splits** the cell it sits in;
- a conditional cannot wrap a row of images or an image-beside-text
  block, because those build their own section and the conditional would
  cut through it;
- a closing tag glued to a list item gets swallowed into the item;
- and the plain-text part cannot align columns it has not seen.

Resolving first makes all of that disappear, because none of it ever
reaches the converter.

The cost is that Inkletter runs on every send rather than once at build
time. It is small — a full conversion of a real newsletter, MJML
compilation included, is a couple of milliseconds — but if you would
rather not have it in the sending path, convert to `.html`/`.txt` files
ahead of time and accept that the templating has to stay simple enough
to survive the trip.

## Notes

- **`{% blocktranslate %}` content stays plain** — whatever is inside is
  formatted by Inkletter afterwards, so keep markup out of the msgid.
- **A `{% verbatim %}` block** is the way to show template syntax in an
  email without Django evaluating it.
- **URL shortening** works as usual: by the time a
  [URL factory](../README.md#url-shortening) sees a link, its tags are
  already resolved into a real URL.
