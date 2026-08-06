# Django template reference

Inkletter can keep Django template tags intact, so that what it produces
is itself a Django template. You build the email once, Django fills in
the data at send time.

Pass `--django` on the command line, or `django_tags=True` from Python.
It is off by default: without it, a stray `{{` in your prose stays a
stray `{{`.

## Why you need the flag

Markdown and MJML are not neutral about curly braces. Without
`--django`, a template tag gets destroyed three different ways:

| You write              | You get                      | Why                                               |
|------------------------|------------------------------|---------------------------------------------------|
| `[Confirm]({{ url }})` | the raw text, no link at all | a Markdown link destination cannot contain spaces |
| `[Confirm]({{url}})`   | `href="%7B%7Burl%7D%7D"`     | the parser percent-encodes the braces             |
| `{% if a < b %}`       | `{% if a &lt; b %}`          | the `<` gets HTML-escaped                         |
| `{{ price*2*qty }}`    | `{{ price<em>2</em>qty }}`   | the asterisks read as emphasis                    |

With the flag, every tag comes out **byte for byte** as you wrote it.

## Quick start

Write one Markdown source, `welcome_email.md`:

```markdown
![Logo]({{ logo_url }})

# Welcome aboard, {{ user.first_name }}

Thanks for signing up. One click and you are in.

**[Activate your account]({% url 'activate' token %})**

See you inside,
The crew.
```

Build both halves of the email:

```bash
inkletter md2html welcome_email.md --django -o templates/welcome_email.html
inkletter md2txt  welcome_email.md --django -o templates/welcome_email.txt
```

Then send it the way you always do:

```python
from django.template.loader import render_to_string

params = {"user": user, "logo_url": settings.LOGO_URL, "token": token}
user.email_user(
    subject="Welcome to Acme",
    html_message=render_to_string("welcome_email.html", params),
    message=render_to_string("welcome_email.txt", params),
)
```

**Both outputs matter.** `md2html` and `md2txt` produce two templates
from the same source, rendered with the same context, and sent together
as `multipart/alternative`. The text half is what keeps you out of spam
folders and what watches, screen readers and text clients actually show.
Every example below applies to both.

## What is supported

✅ works · ⚠️ works with a caveat · ❌ not supported

### Variables and filters

|   |                                                                                                  |
|---|--------------------------------------------------------------------------------------------------|
| ✅ | `{{ var }}`, `{{ user.name }}`, `{{ items.0 }}`                                                  |
| ✅ | filters and their arguments: `{{ name\|title }}`, `{{ date\|date:"d/m/Y" }}`, chained            |
| ❌ | a closing `}}` inside a quoted filter argument: `{{ x\|default:"a}}b" }}` cuts at the first `}}` |

### Tags inside your content

|   |                                                                                            |
|---|--------------------------------------------------------------------------------------------|
| ✅ | `{% url 'name' arg %}` as a link destination                                               |
| ✅ | `{% static 'img/logo.png' %}` as an image source                                           |
| ✅ | `{% now %}`, `{% firstof %}`, `{% cycle %}`, `{% widthratio %}`, `{% trans %}` and friends |
| ✅ | `{% if %}…{% endif %}` in the middle of a sentence                                         |

### Flow control around blocks

|    |                                                                                                    |
|----|----------------------------------------------------------------------------------------------------|
| ✅  | `{% if %}` / `{% for %}` on their own lines, around paragraphs and buttons                         |
| ✅  | a loop around a **whole table**                                                                    |
| ⚠️ | a loop around a **list item**: valid, but each pass makes its own one-item list                    |
| ❌  | a loop around **table rows**: the row falls out of the table                                       |
| ❌  | a conditional around a row of images or an image-beside-text block                                 |
| ⚠️ | a lone statement inside a list, quote or table cell: it stays inline instead of wrapping the block |

### Template structure

|    |                                                                                                              |
|----|--------------------------------------------------------------------------------------------------------------|
| ✅  | `{% load i18n %}` at the top                                                                                 |
| ✅  | `{# comments #}` and `{% comment %}…{% endcomment %}`                                                        |
| ✅  | `{% verbatim %}`, `{% spaceless %}`, `{% filter %}`, `{% autoescape %}`                                      |
| ⚠️ | `{% include %}`: passed through, but the included HTML gets none of Inkletter's styling or responsiveness    |
| ⚠️ | `{% blocktranslate %}`: the extracted msgid will contain the generated HTML — keep the wrapped content plain |
| ❌  | `{% extends %}`, `{% block %}`: pointless here, the output is already a complete template                    |
| ❌  | a tag spread over several lines — Django does not allow it either                                            |

## Two layout rules

### Statements go on their own line

A statement alone on its line wraps whole blocks. Inside a sentence, it
stays inside the paragraph — which is what you want for a short
conditional.

```markdown
{% if trial_ending %}

Your trial ends on {{ end_date }}.

**[Pick a plan]({% url 'plans' %})**

{% endif %}
```

### Leave a blank line before a closing tag that follows a list

This is the one that bites. Markdown's lazy continuation swallows a
closing tag glued to a list item, and your `{% endfor %}` ends up
*inside* the last bullet — the template still renders, but the loop
never closes where you meant it to.

```markdown
<!-- broken: {% endfor %} is absorbed into the last item -->
{% for feature in features %}

- {{ feature }}
  {% endfor %}

<!-- correct -->
{% for feature in features %}

- {{ feature }}

{% endfor %}
```

When in doubt, put a blank line on both sides of every statement line.

## Limitations worth knowing

- **A loop cannot repeat table rows.** Markdown parses tables line by
  line, so a looped row leaves the table and becomes a paragraph. Loop
  around the whole table instead — that works, and it is what you want
  in an email anyway.
- **A conditional cannot wrap a row of images or an image-beside-text
  block.** Those build their own section, and the conditional would cut
  through it. Conditionals around paragraphs, buttons, tables, lists and
  single images are all fine.
- **`md2mjml --django` gives you a Django template of MJML**, not MJML
  you can compile straight away: a tag containing `<` is valid Django
  but not valid XML. Render it with Django first, or just use `md2html`,
  which compiles before putting the tags back.
- **Tags in code blocks are left alone by Inkletter** — but Django will
  still evaluate them at send time. Wrap them in `{% verbatim %}` if you
  are documenting template syntax.

## Two Django gotchas

**Turn autoescaping off in the text template.** Django escapes for HTML
even in a `.txt`, so a customer named `Ben & Jerry` reads as
`Ben &amp; Jerry` in the plain-text half of your email:

```markdown
{% autoescape off %}

Sent by {{ company }}.

{% endautoescape %}
```

**Keep `{% blocktranslate %}` content plain.** Whatever is inside gets
formatted by Inkletter first, so the msgid `makemessages` extracts will
contain the generated HTML — which your translators will not thank you
for.

## URL shortening

If you use a [URL factory](../README.md#url-shortening), URLs holding a
template tag are left alone: they are not resolved yet, so there is
nothing a shortener could usefully do with them, and calling the API
would burn quota for a link that cannot work. Plain URLs in the same
document are still rewritten as usual.
