from inkletter.md_to_html_fragment import parse_markdown_to_html_fragment


def test_full_document_covers_every_markdown_element():
    # the document of the text output's own test, every construct of the language in one document: ATX headings h1-h6,
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
    actual = parse_markdown_to_html_fragment(markdown_input)
    print(actual)
    assert actual == (
        "<h1>The Inkletter Times</h1>"
        "<p>A paragraph with <em>emphasis</em>, <strong>strong</strong>, <s>strikethrough</s>, <code>code span</code>,<br>a soft break and a hard break<br>right here.</p>"
        '<p>Special: an entity AT&amp;T, a copyright ©, an escaped *star*,<br>an inline html tag and an autolink <a href="https://example.com">https://example.com</a>.</p>'
        "<h2>Setext heading</h2>"
        '<p>Visit <a href="https://example.com">our site</a>, a titled <a href="https://example.com/guide">guide</a>,<br>or the bare link <a href="https://example.com">https://example.com</a>.</p>'
        "<h3>Level three</h3>"
        "<h4>Level four</h4>"
        "<h5>Level five</h5>"
        "<h6>Level six</h6>"
        "<hr>"
        "<blockquote><p>A quote on two<br>lines.</p><blockquote><p>A nested quote.</p></blockquote><ul><li>a list in a quote</li><li>with two items</li></ul></blockquote>"
        '<pre><code>def hello(name):\n    print("hi", name)\n\nhello("world")</code></pre>'
        "<pre><code>an indented code block</code></pre>"
        "<ol><li>first ordered item</li><li>second one,<br>soft-wrapped</li><li>renumbered anyway</li></ol>"
        '<ul><li>unordered item<ul><li>nested item</li></ul></li><li style="list-style-type: none">☑ a done task</li><li style="list-style-type: none">☐ a pending task</li><li>a <strong><a href="https://example.com/list">bold link in a list</a></strong> stays a link</li></ul>'
        '<table><thead><tr><th style="text-align: left">Left</th><th style="text-align: center">Center</th><th style="text-align: right">Right</th></tr></thead><tbody><tr><td style="text-align: left">ab</td><td style="text-align: center">cd</td><td style="text-align: right">ef</td></tr><tr><td style="text-align: left">a <strong>bold</strong> cell</td><td style="text-align: center">x</td><td style="text-align: right">12345</td></tr></tbody></table>'
        '<p>First view<br>Second view<br><a href="https://example.com">Logo</a></p>'
        "<p>Portrait</p>"
        "<p>Jane joined the team this week.<br>She will own the rendering platform.</p>"
        '<p><a href="https://example.com/story"><strong>Read the full story</strong></a></p>'
    )
