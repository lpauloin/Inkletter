// What Inkletter teaches markdown-it to read, beyond CommonMark —
// `inkletter/plugins/__init__.py`: one module per plugin, each adding one
// rule; `createMarkdown` decides which ones a document gets.
//
// | Plugin                 | Module            | Rule            | What it reads                         |
// |------------------------|-------------------|-----------------|---------------------------------------|
// | `hashtagPlugin`        | `hashtags`        | inline, `#`     | `#tag`, before any mark inside it     |
// | `bareLinksPlugin`      | `bare_links`      | inline, `:`;    | `https://…`, at its `:`; `exemple.com`|
// |                        |                   | core            | in the text                           |
// | `taskListsPlugin`      | `task_lists`      | core            | `[ ]` and `[x]` opening a list item   |
// | `typedListsPlugin`     | `typed_lists`     | block, ends `p` | a list ends where its author stopped  |
// | `linkAttributesPlugin` | `link_attributes` | inline, `{`     | `{width=96px}` after an image         |

export { bareLinksPlugin } from './bare_links.js';
export { hashtagPlugin } from './hashtags.js';
export { linkAttributesPlugin } from './link_attributes.js';
export { taskListsPlugin } from './task_lists.js';
export { typedListsPlugin } from './typed_lists.js';
