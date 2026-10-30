// Renders the normalized tree as a fragment of HTML — the inside of a
// document, to be set inside another one — `inkletter/visitors/htmlgen.py`.
//
// No theme applies: the page around the fragment styles it — of the
// annotations, only the hand-written anchors and a task's box are read.
// Safe to set inside a page that trusts nothing the author typed: every
// text is escaped, raw HTML is dropped, a target that runs something is
// never a link (`runsSomething`), and an image is its alternative text. A hand-written anchor is a link, its tag rebuilt from its address
// alone. A line break the author typed stays one.

import {
  type BlockCode,
  type BlockQuote,
  type BlockText,
  type Button,
  type CodeSpan,
  type Document,
  type Emphasis,
  type Hashtag,
  type Heading,
  type Image,
  type ImageLink,
  type ImageRow,
  type InlineHtml,
  Link,
  type List,
  type ListItem,
  type LiteralText,
  type MediaObject,
  type Mention,
  type Node,
  type Paragraph,
  type StrikeThrough,
  type Strong,
  type Table,
  type TableCell,
  type TableHeader,
  type TableRow,
  type TaskListItem,
} from '../ast.js';
import { htmlEscape } from '../stdlib.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';


export class HtmlFragmentCodegen extends NodeVisitor {
  parts: string[] = [];
  // Hand-written anchors opened and not closed yet: the block they sit in
  // closes them, whatever the author forgot.
  openAnchors = 0;

  getHtml(): string {
    return this.parts.join('');
  }

  write(html: string): void {
    this.parts.push(html);
  }

  text(value: string): void {
    this.write(htmlEscape(value, false));
  }

  wrapped(tag: string, node: Node, scope: ScopeStack, attributes = ''): void {
    const start = this.parts.length;
    this.write(`<${tag}${attributes}>`);
    this.checkbox(node);
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
    this.wrapped('p', node, scope);
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    // the text of a tight list's item: no paragraph of its own
    this.checkbox(node);
    this.genericVisit(node, scope);
  }

  /** The box a task item's first line opens on. */
  checkbox(node: Node): void {
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
    this.write('<code>');
    this.text(node.code);
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
    this.wrapped('s', node, scope);
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

  visit_Mention(node: Mention, scope: ScopeStack): void {
    // someone named: their name, never their URN
    this.genericVisit(node, scope);
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
    if (node.saysSomething) this.text(node.altText);
  }

  visit_ImageLink(node: ImageLink): void {
    // its alternative text, as the link it was
    if (!node.saysSomething) return;
    this.write(`<a href="${htmlEscape(node.href)}">`);
    this.text(node.img.altText);
    this.write('</a>');
  }

  visit_ImageRow(node: ImageRow, scope: ScopeStack): void {
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
    // the image's alternative text, then the text beside it
    if (node.image.saysSomething) {
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
    const tag = node.ordered ? 'ol' : 'ul';
    const start = node.ordered && node.start !== null && node.start !== 1 ? ` start="${node.start}"` : '';
    this.write(`<${tag}${start}>`);
    this.genericVisit(node, scope);
    this.write(`</${tag}>`);
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
    const align = node.align && ['left', 'center', 'right'].includes(node.align) ? ` style="text-align: ${node.align}"` : '';
    this.wrapped(tag, node, scope, align);
  }
}
