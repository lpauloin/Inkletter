// Renders the normalized tree as the plain-text email alternative —
// `inkletter/visitors/textgen.py`. Sibling of the MJML codegen, on the same
// CodeBlock machinery, and the base of the LinkedIn output, which keeps its
// lines and changes its choices. A fragment that needs a width before
// landing in the output is visited into a nested CodeBlock, resolved,
// shaped, then written.

import {
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
  type Link,
  type List,
  type LiteralText,
  type MailLink,
  type MediaObject,
  type Node,
  type Paragraph,
  type StrikeThrough,
  type Strong,
  type Table,
  type TableCell,
  type TelLink,
  type BlockCode,
  TaskListItem,
  type UrlLink,
} from '../ast.js';
import { CodeBlock, CodeBlockResolver, Newline, TextElement } from '../codeblock.js';
import { isSpelledBy } from '../plugins/bare_domains.js';
import { center, codePoints, ljust, rjust, rstrip, splitLines, strip } from '../stdlib.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';

const DIVIDER = '-'.repeat(40);
const BULLET = '- ';

export class TextCodegen extends NodeVisitor {
  root = new CodeBlock();
  resolver = new CodeBlockResolver();
  current = this.root;

  constructor(protected readonly bullet = BULLET) {
    super();
  }

  getText(): string {
    const text = this.resolver.resolve(this.root);
    return text ? `${text}\n` : '';
  }

  /** Every piece of text goes through here, so that an output built on this
   *  one can say something about what it writes. */
  write(text: string): void {
    this.current.addText(text);
  }

  line(text = ''): void {
    if (text) this.write(text);
    this.current.addNewline();
  }

  /** End the current line if the last element left it open. */
  closeLine(): void {
    for (let at = this.current.elements.length - 1; at >= 0; at -= 1) {
      const element = this.current.elements[at];
      if (element instanceof Newline || element instanceof CodeBlock) return; // nested blocks are always attached closed
      if (element instanceof TextElement) {
        this.current.addNewline();
        return;
      }
    }
  }

  /** The node's output as its own CodeBlock, line closed. */
  renderBlock(node: Node, scope: ScopeStack): CodeBlock {
    return this.nested(() => {
      this.visit(node, scope);
      this.closeLine();
    });
  }

  /** Emit the visible blocks separated by one blank line. */
  emitBlocks(nodes: Node[], scope: ScopeStack): void {
    const visible = nodes.map((node) => this.renderBlock(node, scope)).filter((block) => block.elements.length);
    visible.forEach((block, index) => {
      if (index) this.line();
      this.current.addCodeblock(block);
    });
  }

  /** Divert what `fill` writes into a fresh CodeBlock, then restore. */
  nested(fill: () => void): CodeBlock {
    const parent = this.current;
    const block = new CodeBlock();
    this.current = block;
    fill();
    this.current = parent;
    return block;
  }

  /** Flat text of inline nodes (labels, cells), via a nested block. */
  resolveInline(nodes: Node[], scope: ScopeStack): string {
    const block = this.nested(() => {
      for (const node of nodes) this.visit(node, scope);
    });
    return strip(this.resolver.resolve(block));
  }

  visit_Document(node: Document, scope: ScopeStack): void {
    this.emitBlocks(node.children, scope);
  }

  // --- Blocks ---

  visit_Paragraph(node: Paragraph, scope: ScopeStack): void {
    this.genericVisit(node, scope);
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    this.genericVisit(node, scope);
    this.line();
  }

  visit_Heading(node: Heading, scope: ScopeStack): void {
    const block = this.nested(() => {
      for (const child of node.children) this.visit(child, scope);
    });
    const title = this.resolver.resolve(block);
    const lines = splitLines(title);
    for (const line of lines) this.line(line);
    const width = Math.max(0, ...lines.map(codePoints));
    if (node.level === 1 && width) this.line('='.repeat(width));
    else if (node.level === 2 && width) this.line('-'.repeat(width));
  }

  visit_BlockQuote(node: BlockQuote, scope: ScopeStack): void {
    // the marker is a prefix on every line of the quote, blank ones included
    this.current.addIndent('> ');
    this.emitBlocks(node.children, scope);
    this.current.addDedent();
  }

  visit_BlockCode(node: BlockCode): void {
    for (const line of splitLines(node.code)) this.line(line ? `    ${line}` : '');
  }

  visit_ThematicBreak(): void {
    this.line(DIVIDER);
  }

  visit_BlankLine(): void {}

  visit_BlockHtml(): void {} // a raw HTML block has no reliable text rendering

  // --- Inline ---

  visit_LiteralText(node: LiteralText): void {
    this.write(node.value);
  }

  visit_CodeSpan(node: CodeSpan): void {
    this.write(node.code);
  }

  visit_Hashtag(node: Hashtag): void {
    this.write(`#${node.name}`);
  }

  visit_InlineHtml(node: InlineHtml): void {
    // the tags vanish — except a closing anchor, which spells out the URL
    // its opening tag carried, exactly as a Markdown link does
    const href = node.annotations.anchor_href;
    if (typeof href === 'string' && href) this.write(` <${href}>`);
  }

  visit_Emphasis(node: Emphasis, scope: ScopeStack): void {
    this.genericVisit(node, scope);
  }

  visit_Strong(node: Strong, scope: ScopeStack): void {
    this.genericVisit(node, scope);
  }

  visit_StrikeThrough(node: StrikeThrough, scope: ScopeStack): void {
    this.genericVisit(node, scope);
  }

  visit_UrlLink(node: UrlLink, scope: ScopeStack): void {
    const label = this.resolveInline(node.children, scope);
    if (!label || isSpelledBy(node.href, label)) this.write(node.href);
    else this.write(`${label} <${node.href}>`);
  }

  visit_MailLink(node: MailLink, scope: ScopeStack): void {
    this.named(node, node.address, scope);
  }

  visit_TelLink(node: TelLink, scope: ScopeStack): void {
    this.named(node, node.number, scope);
  }

  named(node: Link, target: string, scope: ScopeStack): void {
    // the address or the number alone when the label is it, rather than
    // twice, once with its scheme
    const label = this.resolveInline(node.children, scope);
    if (!label || label === target || label === node.href) this.write(target);
    else this.write(`${label} <${node.href}>`);
  }

  visit_LineBreak(): void {
    this.line();
  }

  visit_SoftBreak(): void {
    this.line();
  }

  // --- Images and layout conventions ---

  visit_Image(node: Image): void {
    if (node.altText) this.line(node.altText);
  }

  visit_ImageLink(node: ImageLink): void {
    const alt = node.img.altText;
    this.line(alt ? `${alt} <${node.href}>` : node.href);
  }

  visit_ImageRow(node: ImageRow, scope: ScopeStack): void {
    for (const image of node.children) this.visit(image, scope);
  }

  visit_MediaObject(node: MediaObject, scope: ScopeStack): void {
    this.visit(node.image, scope);
    if (this.current.elements.length) this.line(); // blank line only below a visible alt
    this.emitBlocks(node.children, scope);
  }

  visit_Button(node: Button, scope: ScopeStack): void {
    const label = strip(this.resolveInline(node.children, scope).replaceAll('\n', ' '));
    // a bare address made a button reads as the address, once
    this.line(isSpelledBy(node.href, label) ? `→ ${node.href}` : `→ ${label} : ${node.href}`);
  }

  // --- Lists ---

  visit_List(node: List, scope: ScopeStack): void {
    let number = node.ordered && node.start ? node.start : 1;
    for (const item of node.elements) {
      let marker: string;
      if (item instanceof TaskListItem) marker = item.checked ? '[x] ' : '[ ] ';
      else if (node.ordered) {
        marker = `${number}. `;
        number += 1;
      } else marker = this.bullet;
      this.write(marker);
      this.current.addIndent();
      for (const child of item.children) this.visit(child, scope);
      this.closeLine();
      this.current.addDedent();
    }
  }

  // --- Tables ---

  cellText(cell: TableCell, scope: ScopeStack): string {
    return strip(this.resolveInline(cell.children, scope).replaceAll('\n', ' '));
  }

  visit_Table(node: Table, scope: ScopeStack): void {
    const header = node.header?.headers ?? [];
    const rows = node.rows.map((row) => row.row);
    const aligns = (header.length ? header : (rows[0] ?? [])).map((cell) => cell.align);
    const grid = header.length ? [header.map((cell) => this.cellText(cell, scope))] : [];
    grid.push(...rows.map((row) => row.map((cell) => this.cellText(cell, scope))));
    if (!grid.length) return;
    const columns = Math.max(...grid.map((line) => line.length));
    const widths = Array.from({ length: columns }, (_, at) => Math.max(...grid.map((line) => codePoints(line[at] ?? ''))));
    const emitRow = (line: string[]) => {
      const padded = widths.map((width, at) => pad(line[at] ?? '', width, aligns[at] ?? null));
      this.line(rstrip(padded.join(' | ')));
    };
    let body = grid;
    if (header.length && grid[0]) {
      emitRow(grid[0]);
      this.line(widths.map((width) => '-'.repeat(width)).join('-+-'));
      body = grid.slice(1);
    }
    for (const line of body) emitRow(line);
  }
}

function pad(value: string, width: number, align: string | null): string {
  if (align === 'right') return rjust(value, width);
  if (align === 'center') return center(value, width);
  return ljust(value, width);
}
