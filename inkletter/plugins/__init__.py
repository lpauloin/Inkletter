"""What Inkletter teaches markdown-it to read, beyond CommonMark.

One module per plugin, each adding one rule; `create_markdown` decides
which ones a document gets.

| Plugin                   | Module            | Rule            | What it reads                         |
|--------------------------|-------------------|-----------------|---------------------------------------|
| `hashtag_plugin`         | `hashtags`        | inline, `#`     | `#tag`, before any mark inside it     |
| `bare_links_plugin`      | `bare_links`      | core            | `https://…` and `exemple.com`         |
| `task_lists_plugin`      | `task_lists`      | core            | `[ ]` and `[x]` opening a list item   |
| `typed_lists_plugin`     | `typed_lists`     | block, ends `p` | a list ends where its author stopped  |
| `link_attributes_plugin` | `link_attributes` | inline, `{`     | `{width=96px}` after an image         |

`bare_domains` is the grammar of a domain written without its scheme, which
`bare_links` reads and the outputs ask about a label.
"""

from inkletter.plugins.bare_links import bare_links_plugin
from inkletter.plugins.hashtags import hashtag_plugin
from inkletter.plugins.link_attributes import link_attributes_plugin
from inkletter.plugins.task_lists import task_lists_plugin
from inkletter.plugins.typed_lists import typed_lists_plugin

__all__ = [
    "bare_links_plugin",
    "hashtag_plugin",
    "link_attributes_plugin",
    "task_lists_plugin",
    "typed_lists_plugin",
]
