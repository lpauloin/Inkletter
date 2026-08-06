from inkletter.md_to_text import parse_markdown_to_text


def test_full_document_covers_every_markdown_element():
    # every construct of the language in one document: ATX headings h1-h6,
    # a setext heading, emphasis/strong/strikethrough/code span, soft and
    # hard breaks, entities, escapes, inline html, autolinks, links (plain,
    # titled, bare), thematic break, blockquote (nested, with a list),
    # fenced and indented code, ordered (with renumbering) / unordered /
    # nested / task lists, a bold link in a list, an aligned table with
    # formatting, an image row with a linked image, a media object, an
    # alt-less image, a raw html block, and a button
    markdown_input = """\
# The Inkletter Times

A paragraph with *emphasis*, **strong**, ~~strikethrough~~, `code span`,
a soft break and a hard break\\
right here.

Special: an entity AT&amp;T, a copyright &copy;, an escaped \\*star\\*,
an <span>inline html tag</span> and an autolink <https://example.com>.

Setext heading
--------------

Visit [our site](https://example.com), a titled [guide](https://example.com/guide "The guide"),
or the bare link [https://example.com](https://example.com).

### Level three

#### Level four

##### Level five

###### Level six

---

> A quote on two
> lines.
>
> > A nested quote.
>
> - a list in a quote
> - with two items

```python
def hello(name):
    print("hi", name)

hello("world")
```

    an indented code block

1. first ordered item
2. second one,
   soft-wrapped
7. renumbered anyway

- unordered item
  - nested item
- [x] a done task
- [ ] a pending task
- a **[bold link in a list](https://example.com/list)** stays a link

| Left | Center | Right |
|:-----|:------:|------:|
| ab | cd | ef |
| a **bold** cell | x | 12345 |

![First view](https://x.com/a.png) ![Second view](https://x.com/b.png) [![Logo](https://x.com/l.png)](https://example.com)

![Portrait](https://x.com/team.png) Jane joined the team this week.
She will own the rendering platform.

![](https://x.com/decorative.png)

<div>a raw html block</div>

**[Read the full story](https://example.com/story)**
"""
    actual = parse_markdown_to_text(markdown_input)
    print(actual)
    assert actual == """\
THE INKLETTER TIMES
===================

A paragraph with emphasis, strong, strikethrough, code span,
a soft break and a hard break
right here.

Special: an entity AT&T, a copyright ©, an escaped *star*,
an inline html tag and an autolink https://example.com.

Setext heading
--------------

Visit our site <https://example.com>, a titled guide <https://example.com/guide>,
or the bare link https://example.com.

Level three

Level four

Level five

Level six

----------------------------------------

> A quote on two
> lines.
>
> > A nested quote.
>
> - a list in a quote
> - with two items

    def hello(name):
        print("hi", name)

    hello("world")

    an indented code block

1. first ordered item
2. second one,
  soft-wrapped
3. renumbered anyway

- unordered item
  - nested item
[x] a done task
[ ] a pending task
- a bold link in a list <https://example.com/list> stays a link

Left        | Center | Right
------------+--------+------
ab          |   cd   |    ef
a bold cell |   x    | 12345

First view
Second view
Logo <https://example.com>

Portrait

Jane joined the team this week.
She will own the rendering platform.

→ Read the full story : https://example.com/story
"""
