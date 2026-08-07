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

## The whole integration

```python
import re

from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.template.loader import get_template

from inkletter import parse_markdown_to_html, parse_markdown_to_text


def send_markdown_email(template_name, context, subject, to):
    """Render a Markdown template, convert it, send both parts."""
    source = get_template(template_name).template.source
    # autoescape off: this render produces *Markdown*, not HTML, so
    # escaping for HTML here would put &amp; in front of your reader
    markdown = Template(
        "{% autoescape off %}" + source + "{% endautoescape %}"
    ).render(Context(context))

    message = EmailMultiAlternatives(
        subject, parse_markdown_to_text(markdown), to=to
    )
    message.attach_alternative(parse_markdown_to_html(markdown), "text/html")
    message.send()
```

Pass a `theme=` to either converter if you do not want the default one.

## Escape what comes from your users

A value now lands in a **Markdown** document, so a member called `_Bob_`
reaches the reader in italics, and a folder named `Invoices | Q3` splits
the table cell it sits in. Django's own escaping guards HTML and helps
with neither.

Register a filter in your app — `yourapp/templatetags/markdown_safe.py`:

```python
import re

from django import template

register = template.Library()

# CommonMark lets any ASCII punctuation be backslash-escaped. Escape the
# whole set: guessing which characters are dangerous in which position
# is how you miss one. The backslashes disappear at parse time, so the
# reader of the text part never sees them.
PUNCTUATION = re.compile(r"([!-/:-@\[-`{-~])")


@register.filter(name="md")
def md(value):
    """Make a value literal once it lands in a Markdown document."""
    return PUNCTUATION.sub(r"\\\1", str(value))
```

Then put it last in every chain that carries user data:

```django
{% load markdown_safe %}

Hi {{ member.first_name|default:'there'|md }},
```

Your own words — the ones you wrote in the template — need no filter.
Only the data does.

## A complete example

```django
{% load markdown_safe %}# Storage limits are changing

Hi {{ member.first_name|default:'there'|md }},

| Folder | Keeps for |
|---|---|
{% for f in folders %}| {{ f.name|md }} | {{ f.days|default:"no limit"|md }} |
{% endfor %}

In **{{ grace_days }} days** those folders revert.

{% if paid %}
Thanks for being on a paid plan.
{% else %}
**[See the plans]({% url 'plans' %})**
{% endif %}
```

The HTML part gets a themed table with one row per folder. The text
part gets the same table, its columns aligned on the **real values**:

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
pair of Django templates you could commit — but the tags would then
have to survive Markdown, MJML and an XML compiler, and they do not
survive intact:

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

- **Turn autoescaping off** for the render, as in the snippet. Django
  escapes for HTML even in a `.txt`, so without it a customer named
  `Ben & Jerry` reads as `Ben &amp; Jerry`.
- **`{% blocktranslate %}` content stays plain** — whatever is inside is
  formatted by Inkletter afterwards, so keep markup out of the msgid.
- **A `{% verbatim %}` block** is the way to show template syntax in an
  email without Django evaluating it.
- **URL shortening** works as usual: by the time a
  [URL factory](../README.md#url-shortening) sees a link, its tags are
  already resolved into a real URL.
