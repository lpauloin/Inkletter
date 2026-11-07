// Renders the normalized tree as a fragment of HTML — the inside of a
// document, to be set inside another one — `inkletter/visitors/htmlgen.py`.
//
// No theme applies: the page around the fragment styles it — of the
// annotations, only the hand-written anchors and a task's box are read.
// Safe to set inside a page that trusts nothing the author typed: every
// text is escaped, raw HTML is dropped, a target that runs something is
// never a link (`runsSomething`), and an image is its alternative text —
// unless the caller asks for the pictures (`images`), for a page that
// serves them itself: then an image with a web address (`http`, `https`)
// or carried inside the page (`data:image/…`) is an `<img>`, one alone on
// its line a `<figure>` with its title as `<figcaption>`, and any other
// address stays its alternative text. A hand-written anchor is a link, its
// tag rebuilt from its address alone. A line break the author typed stays
// one.
//
// For a page or an editor that wants them, three more, each asked for:
//
// | Option           | What the fragment writes                               |
// |------------------|--------------------------------------------------------|
// | `mentions`       | each mention as an anchor with the attributes the      |
// |                  | caller's function gives for its URN — an address to a  |
// |                  | public page, an entity an editor reads back —, `@name` |
// |                  | when it gives none or a set the rules below refuse     |
// |                  | (`anchorAttributes`); without it, a mention is its     |
// |                  | name                                                   |
// | `unicodeStrike`  | strikethrough in its Unicode look-alike, not `<s>`     |
// | `taskParagraphs` | a list holding tasks as a paragraph per item, its box  |
// |                  | or its marker in its text, not a list                  |

import {
  type BlockCode,
  type BlockQuote,
  BlockText,
  type Button,
  type CodeSpan,
  type Document,
  type Emphasis,
  type Hashtag,
  type Heading,
  Image,
  ImageLink,
  type ImageRow,
  type InlineHtml,
  Link,
  type List,
  type ListItem,
  type LiteralText,
  type MediaObject,
  type Mention,
  type Node,
  Paragraph,
  type StrikeThrough,
  type Strong,
  type Table,
  type TableCell,
  type TableHeader,
  type TableRow,
  TaskListItem,
  runsSomething,
} from '../ast.js';
import { htmlEscape, strip } from '../stdlib.js';
import { NodeVisitor } from './generic.js';
import { strike } from '../lookalikes.js';
import type { ScopeStack } from './scope.js';

/** The attributes of a mention's anchor, by its URN; `null` or `undefined`
 *  for `@name`. */
export type MentionAttributes = (urn: string) => Record<string, string> | null | undefined;

// The attributes a caller may give a mention's anchor (`mentions`): a set
// breaking any rule is refused whole, and the mention goes out as `@name`.
//
// | Rule                                                  | Refused, e.g.          |
// |-------------------------------------------------------|------------------------|
// | a name is a letter, then letters, digits or `-`;      | `x onmouseover=y`,     |
// | written lower-cased, once                             | `xlink:href`           |
// | no event handler                                      | `onclick`              |
// | an address never runs something (`runsSomething`)     | `href="javascript:…"`  |
// | a value is a string, escaped                          | `3`, `null`            |
const ATTRIBUTE_NAME = /^[a-z][a-z0-9-]*$/;
const URL_ATTRIBUTES = ['href', 'src', 'action', 'formaction'];

/** The attributes of a mention's anchor as written in its tag, or null for
 *  `@name`: none given, none at all, or a set breaking a rule. */
export function anchorAttributes(attributes: Record<string, string> | null | undefined): string | null {
  if (attributes === null || attributes === undefined) return null;
  const entries = Object.entries(attributes);
  if (!entries.length) return null;
  const written = new Map<string, string>();
  for (const [key, value] of entries) {
    if (typeof value !== 'string') return null;
    const name = key.toLowerCase();
    if (!ATTRIBUTE_NAME.test(name) || name.startsWith('on') || written.has(name)) return null;
    if (URL_ATTRIBUTES.includes(name) && runsSomething(value)) return null;
    written.set(name, value);
  }
  return [...written].map(([name, value]) => ` ${name}="${htmlEscape(value)}"`).join('');
}

export class HtmlFragmentCodegen extends NodeVisitor {
  parts: string[] = [];
  images: boolean;
  /** The attributes of a mention's anchor, by its URN, or null for `@name`. */
  mentions: MentionAttributes | null;
  unicodeStrike: boolean;
  taskParagraphs: boolean;
  // Inside a strikethrough written as its look-alike.
  striking = false;
  // The struck texts of the strikethrough being written, by the place each
  // holds in `parts`: struck once it closes, each space reading its real
  // neighbours across tags.
  struck: [number, string][] = [];
  // What opens the first line of a list's item written as paragraphs.
  marker = '';
  // Hand-written anchors opened and not closed yet: the block they sit in
  // closes them, whatever the author forgot.
  openAnchors = 0;

  constructor(
    images = false,
    mentions: MentionAttributes | null = null,
    unicodeStrike = false,
    taskParagraphs = false,
  ) {
    super();
    this.images = images;
    this.mentions = mentions;
    this.unicodeStrike = unicodeStrike;
    this.taskParagraphs = taskParagraphs;
  }

  getHtml(): string {
    return this.parts.join('');
  }

  write(html: string): void {
    this.parts.push(html);
  }

  text(value: string): void {
    if (this.striking && value) this.struck.push([this.parts.length, value]);
    this.write(htmlEscape(value, false));
  }

  wrapped(tag: string, node: Node, scope: ScopeStack, attributes = ''): void {
    const start = this.parts.length;
    this.write(`<${tag}${attributes}>`);
    this.lineOpening(node);
    const opened = this.openAnchors;
    this.openAnchors = 0;
    this.genericVisit(node, scope);
    this.write('</a>'.repeat(this.openAnchors));
    this.openAnchors = opened;
    if (tag === 'p' && this.parts.slice(start + 1).join('') === '') {
      // a paragraph with nothing to read — an image without its alternative
      // text — leaves nothing behind
      this.parts.splice(start);
      return;
    }
    this.write(`</${tag}>`);
  }

  // --- Blocks ---

  visit_Document(node: Document, scope: ScopeStack): void {
    this.genericVisit(node, scope);
  }

  visit_Paragraph(node: Paragraph, scope: ScopeStack): void {
    const only = this.shownAlone(node);
    if (only !== null) {
      this.figure(only);
      return;
    }
    this.wrapped('p', node, scope);
  }

  // --- Pictures, when asked for ---

  /** Whether this image — or the one inside this link — is drawn, rather
   *  than said by its text (`Image.drawable`). */
  shown(image: Image | ImageLink): boolean {
    return this.images && image.picture.drawable;
  }

  /** The one drawn image — linked or not — a paragraph holds and nothing
   *  else, or null. */
  shownAlone(node: Paragraph): Image | ImageLink | null {
    if (node.children.length !== 1) return null;
    const [only] = node.children;
    return (only instanceof Image || only instanceof ImageLink) && this.shown(only) ? only : null;
  }

  draw(image: Image): void {
    this.write(`<img src="${htmlEscape(image.url)}" alt="${htmlEscape(image.altText)}">`);
  }

  /** A drawn image — or linked one — on its own line: laid small when its
   *  author said so, inside its link when it has one, its title under it. */
  figure(image: Image | ImageLink): void {
    const picture = image.picture;
    this.write(picture.attributes.size === 'small' ? '<figure data-size="small">' : '<figure>');
    if (image instanceof ImageLink) this.write(`<a href="${htmlEscape(image.href)}">`);
    this.draw(picture);
    if (image instanceof ImageLink) this.write('</a>');
    if (picture.title && strip(picture.title)) {
      this.write('<figcaption>');
      this.text(picture.title);
      this.write('</figcaption>');
    }
    this.write('</figure>');
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    // the text of a tight list's item: no paragraph of its own
    this.lineOpening(node);
    this.genericVisit(node, scope);
  }

  /** What a line opens on: the marker of a list's item written as
   *  paragraphs, then the box of a task item's first line. */
  lineOpening(node: Node): void {
    if (this.marker) {
      const marker = this.marker;
      this.marker = '';
      this.text(marker);
    }
    const box = node.annotations.checkbox;
    if (typeof box === 'string' && box) this.text(`${box} `);
  }

  visit_Heading(node: Heading, scope: ScopeStack): void {
    this.wrapped(`h${node.level}`, node, scope);
  }

  visit_BlockQuote(node: BlockQuote, scope: ScopeStack): void {
    this.wrapped('blockquote', node, scope);
  }

  visit_BlockCode(node: BlockCode): void {
    this.write('<pre><code>');
    this.text(node.code);
    this.write('</code></pre>');
  }

  visit_ThematicBreak(): void {
    this.write('<hr>');
  }

  visit_BlankLine(): void {} // between two blocks, the blocks themselves say it

  visit_BlockHtml(): void {}

  // --- Inline ---

  visit_LiteralText(node: LiteralText): void {
    this.text(node.value);
  }

  visit_CodeSpan(node: CodeSpan): void {
    // code stays as written, even inside a strikethrough
    this.write('<code>');
    this.write(htmlEscape(node.code, false));
    this.write('</code>');
  }

  visit_Hashtag(node: Hashtag): void {
    this.text(`#${node.name}`);
  }

  visit_InlineHtml(node: InlineHtml): void {
    // the tags vanish, the text between them stays — except an anchor,
    // rebuilt from its address alone
    if (node.annotations.anchor_nested) return;
    const href = node.annotations.anchor_opens;
    if (typeof href === 'string') {
      this.write(`<a href="${htmlEscape(href)}">`);
      this.openAnchors += 1;
    } else if (node.annotations.anchor_href && this.openAnchors) {
      this.write('</a>');
      this.openAnchors -= 1;
    }
  }

  visit_Emphasis(node: Emphasis, scope: ScopeStack): void {
    this.wrapped('em', node, scope);
  }

  visit_Strong(node: Strong, scope: ScopeStack): void {
    this.wrapped('strong', node, scope);
  }

  visit_StrikeThrough(node: StrikeThrough, scope: ScopeStack): void {
    if (!this.unicodeStrike) {
      this.wrapped('s', node, scope);
      return;
    }
    if (this.striking) {
      this.genericVisit(node, scope);
      return;
    }
    this.striking = true;
    this.genericVisit(node, scope);
    this.striking = false;
    this.strikeWritten();
  }

  /** Each text of the strikethrough just written, struck in place, the texts
   *  around it read for the neighbours of its edges. */
  strikeWritten(): void {
    const values = this.struck.map(([, value]) => value);
    this.struck.forEach(([index, value], at) => {
      this.parts[index] = htmlEscape(strike(value, values[at - 1] ?? '', values[at + 1] ?? ''), false);
    });
    this.struck = [];
  }

  visit_UrlLink(node: Link, scope: ScopeStack): void {
    this.link(node, scope);
  }

  visit_MailLink(node: Link, scope: ScopeStack): void {
    this.link(node, scope);
  }

  visit_TelLink(node: Link, scope: ScopeStack): void {
    this.link(node, scope);
  }

  /** Someone named: their name, never their URN. Asked for (`mentions`): a
   *  mention naming nobody writes nothing, one the caller gives no
   *  attributes for — or attributes the rules refuse (`anchorAttributes`) —
   *  goes out as `@name`, plain text, and any other is an anchor with those
   *  attributes — the name the author wrote. */
  visit_Mention(node: Mention, scope: ScopeStack): void {
    if (this.mentions === null) {
      this.genericVisit(node, scope);
      return;
    }
    const name = node.plainText();
    if (!name) return;
    const written = anchorAttributes(this.mentions(node.urn));
    if (written === null) {
      this.text(`@${name}`);
      return;
    }
    this.write(`<a${written}>`);
    this.text(name);
    this.write('</a>');
  }

  link(node: Link, scope: ScopeStack): void {
    if (node.children.every((child) => child.isBlank())) {
      // nothing to click on: the address is its own label
      this.write(`<a href="${htmlEscape(node.href)}">`);
      this.text(node.href);
      this.write('</a>');
      return;
    }
    this.wrapped('a', node, scope, ` href="${htmlEscape(node.href)}"`);
  }

  visit_LineBreak(): void {
    this.write('<br>');
  }

  visit_SoftBreak(): void {
    this.write('<br>');
  }

  // --- Images and layout conventions ---

  visit_Image(node: Image): void {
    if (this.shown(node)) this.draw(node);
    else if (node.saysSomething) this.text(node.altText);
  }

  visit_ImageLink(node: ImageLink): void {
    if (this.shown(node)) {
      this.write(`<a href="${htmlEscape(node.href)}">`);
      this.draw(node.img);
      this.write('</a>');
      return;
    }
    // its alternative text, as the link it was
    if (!node.saysSomething) return;
    this.write(`<a href="${htmlEscape(node.href)}">`);
    this.text(node.img.altText);
    this.write('</a>');
  }

  visit_ImageRow(node: ImageRow, scope: ScopeStack): void {
    if (node.children.some((child) => this.shown(child))) {
      // the pictures side by side, in one paragraph, apart as in the source
      // — and the text of those not drawn between them
      const kept = node.children.filter((image) => this.shown(image) || image.saysSomething);
      this.write('<p>');
      kept.forEach((image, index) => {
        if (index) this.write(' ');
        this.visit(image, scope);
      });
      this.write('</p>');
      return;
    }
    // one line per image that says something, as the text output does
    const alts = node.children.filter((image) => image.saysSomething);
    if (!alts.length) return;
    this.write('<p>');
    alts.forEach((image, index) => {
      if (index) this.write('<br>');
      this.visit(image, scope);
    });
    this.write('</p>');
  }

  visit_MediaObject(node: MediaObject, scope: ScopeStack): void {
    // the image — or its alternative text —, then the text beside it; a
    // linked one stays inside its link
    if (this.shown(node.image)) {
      this.figure(node.image);
    } else if (node.image.saysSomething) {
      this.write('<p>');
      this.visit(node.image, scope);
      this.write('</p>');
    }
    this.write('<p>');
    for (const child of node.children) this.visit(child, scope);
    this.write('</p>');
  }

  visit_Button(node: Button, scope: ScopeStack): void {
    this.write(`<p><a href="${htmlEscape(node.href)}"><strong>`);
    this.genericVisit(node, scope);
    this.write('</strong></a></p>');
  }

  // --- Lists ---

  visit_List(node: List, scope: ScopeStack): void {
    if (this.taskParagraphs && node.elements.some((item) => item instanceof TaskListItem)) {
      node.elements.forEach((item, index) => {
        const number = (node.start ?? 1) + index;
        const marker = item instanceof TaskListItem ? '' : node.ordered ? `${number}. ` : '• ';
        this.itemParagraphs(item, marker, scope);
      });
      return;
    }
    const tag = node.ordered ? 'ol' : 'ul';
    const start = node.ordered && node.start !== null && node.start !== 1 ? ` start="${node.start}"` : '';
    this.write(`<${tag}${start}>`);
    this.genericVisit(node, scope);
    this.write(`</${tag}>`);
  }

  /** A list's item as paragraphs, its marker — or its box — opening its
   *  first text, tight (`BlockText`) or loose (`Paragraph`). */
  itemParagraphs(item: ListItem | TaskListItem, marker: string, scope: ScopeStack): void {
    item.children.forEach((block, index) => {
      if (index === 0 && (block instanceof BlockText || block instanceof Paragraph)) this.marker = marker;
      if (block instanceof BlockText) {
        this.write('<p>');
        this.visit(block, scope);
        this.write('</p>');
      } else {
        this.visit(block, scope);
      }
      this.marker = '';
    });
  }

  visit_ListItem(node: ListItem, scope: ScopeStack): void {
    this.wrapped('li', node, scope);
  }

  visit_TaskListItem(node: TaskListItem, scope: ScopeStack): void {
    // the box stands for the marker, in a numbered list as in another
    this.wrapped('li', node, scope, ' style="list-style-type: none"');
  }

  // --- Tables ---

  visit_Table(node: Table, scope: ScopeStack): void {
    this.write('<table>');
    if (node.header !== null) {
      this.write('<thead>');
      this.visit(node.header, scope);
      this.write('</thead>');
    }
    this.write('<tbody>');
    for (const row of node.rows) this.visit(row, scope);
    this.write('</tbody></table>');
  }

  visit_TableHeader(node: TableHeader, scope: ScopeStack): void {
    this.write('<tr>');
    this.genericVisit(node, scope);
    this.write('</tr>');
  }

  visit_TableRow(node: TableRow, scope: ScopeStack): void {
    this.write('<tr>');
    this.genericVisit(node, scope);
    this.write('</tr>');
  }

  visit_TableCell(node: TableCell, scope: ScopeStack): void {
    this.cell('td', node, scope);
  }

  visit_TableHeaderCell(node: TableCell, scope: ScopeStack): void {
    this.cell('th', node, scope);
  }

  cell(tag: string, node: TableCell, scope: ScopeStack): void {
    const align =
      node.align && ['left', 'center', 'right'].includes(node.align) ? ` style="text-align: ${node.align}"` : '';
    this.wrapped(tag, node, scope, align);
  }
}
