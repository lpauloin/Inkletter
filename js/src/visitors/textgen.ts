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
  type ListItem,
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
  type TaskListItem,
  type UrlLink,
} from '../ast.js';
import { CodeBlock, CodeBlockResolver, type CodeElement, Newline, TextElement } from '../codeblock.js';
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
  /** Whether the last element left the current line open. */
  lineOpen(): boolean {
    for (let at = this.current.elements.length - 1; at >= 0; at -= 1) {
      const element = this.current.elements[at];
      if (element instanceof Newline || element instanceof CodeBlock) return false; // nested blocks are always attached closed
      if (element instanceof TextElement) return true;
    }
    return false;
  }

  /** End the current line if the last element left it open. */
  closeLine(): void {
    if (this.lineOpen()) this.current.addNewline();
  }

  /** The node's output as its own CodeBlock, line closed. */
  renderBlock(node: Node, scope: ScopeStack): CodeBlock {
    return this.nested(() => {
      this.visit(node, scope);
      this.closeLine();
    });
  }

  /** Emit the visible blocks separated by one blank line. */
  emitBlocks(nodes: Node[], scope: ScopeStack): boolean {
    let written = false;
    for (const node of nodes) {
      if (!written && this.lineOpen()) {
        // the first block continues a line already open — an item's marker,
        // a quote's — and writes what it opens with there
        if (this.wrote(node, scope)) {
          this.closeLine();
          written = true;
        }
        continue;
      }
      const block = this.renderBlock(node, scope);
      if (!showsText(block.elements)) continue;
      if (written) this.line();
      this.current.addCodeblock(block);
      written = true;
    }
    return written;
  }

  /** Visit a node where the writing stands; whether it wrote words. What a
   *  visit that wrote none left — a break, an indent, a quote's mark — is
   *  taken back, the line kept for what comes next. */
  wrote(node: Node, scope: ScopeStack): boolean {
    const before = this.current.elements.length;
    this.visit(node, scope);
    if (showsText(this.current.elements.slice(before))) return true;
    this.current.elements.splice(before);
    return false;
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
    this.closeLine();
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    // a run of a line: whoever holds it ends the line
    this.genericVisit(node, scope);
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
    // the marker is a prefix on every line of the quote, blank ones included;
    // on a line already open (an item's marker), it is written there
    const before = this.current.elements.length;
    if (this.lineOpen()) this.write('> ');
    this.current.addIndent('> ');
    const written = this.emitBlocks(node.children, scope);
    this.current.addDedent();
    // a quote of nothing leaves no mark
    if (!written) this.current.elements.splice(before);
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
    // The label beside the address unless it spells it: compared once a
    // factory has rewritten the address, so a shortened link still says, in
    // words, where it leads.
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
    if (node.annotations.label_is_address) this.write(target);
    else this.write(`${this.resolveInline(node.children, scope)} <${node.href}>`);
  }

  visit_LineBreak(): void {
    this.line();
  }

  visit_SoftBreak(): void {
    this.line();
  }

  // --- Images and layout conventions ---

  visit_Image(node: Image): void {
    if (node.saysSomething) this.write(node.altText);
  }

  visit_ImageLink(node: ImageLink): void {
    this.write(node.saysSomething ? `${node.img.altText} <${node.href}>` : node.href);
  }

  visit_ImageRow(node: ImageRow, scope: ScopeStack): void {
    // one line per image
    for (const image of node.children) {
      this.visit(image, scope);
      this.closeLine();
    }
  }

  visit_MediaObject(node: MediaObject, scope: ScopeStack): void {
    this.visit(node.image, scope);
    if (this.current.elements.length) {
      // blank line only below a visible alt
      this.closeLine();
      this.line();
    }
    this.emitBlocks(node.children, scope);
  }

  visit_Button(node: Button, scope: ScopeStack): void {
    const label = strip(this.resolveInline(node.children, scope).replaceAll('\n', ' '));
    // a bare address made a button reads as the address, once
    this.line(isSpelledBy(node.href, label) ? `→ ${node.href}` : `→ ${label} : ${node.href}`);
  }

  // --- Lists ---

  /** The blank lines written before an item: in a text, none — a list
   *  reads as one block, loose or tight. */
  blankLinesBefore(_node: List, _index: number): number {
    return 0;
  }

  visit_List(node: List, scope: ScopeStack): void {
    node.elements.forEach((item, index) => {
      for (let blank = this.blankLinesBefore(node, index); blank > 0; blank -= 1) this.line();
      this.visit(item, scope);
    });
  }

  visit_ListItem(node: ListItem, scope: ScopeStack): void {
    const number = node.annotations.number;
    this.item(node, typeof number === 'number' ? `${number}. ` : this.bullet, scope);
  }

  visit_TaskListItem(node: TaskListItem, scope: ScopeStack): void {
    this.item(node, node.checked ? '[x] ' : '[ ] ', scope);
  }

  /** An item on its marker, what it holds indented under it. */
  item(node: ListItem | TaskListItem, marker: string, scope: ScopeStack): void {
    this.write(marker);
    this.current.addIndent();
    // a block that writes nothing leaves the line to the next one
    for (const child of node.children) if (this.wrote(child, scope)) this.closeLine();
    // an empty item still ends on its marker's line
    this.closeLine();
    this.current.addDedent();
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
    let body = grid;
    if (header.length && grid[0]) {
      this.row(grid[0], widths, aligns);
      this.line(widths.map((width) => '-'.repeat(width)).join('-+-'));
      body = grid.slice(1);
    }
    for (const line of body) this.row(line, widths, aligns);
  }

  /** One line of a table, each cell padded to its column. */
  row(line: string[], widths: number[], aligns: (string | null)[]): void {
    const padded = widths.map((width, at) => pad(line[at] ?? '', width, aligns[at] ?? null));
    this.line(rstrip(padded.join(' | ')));
  }
}

function pad(value: string, width: number, align: string | null): string {
  if (align === 'right') return rjust(value, width);
  if (align === 'center') return center(value, width);
  return ljust(value, width);
}

/** Whether elements hold words a reader sees, nested blocks included. */
export function showsText(elements: readonly CodeElement[]): boolean {
  return elements.some(
    (element) =>
      (element instanceof TextElement && Boolean(strip(element.text))) ||
      (element instanceof CodeBlock && showsText(element.elements)),
  );
}
