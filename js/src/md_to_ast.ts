// From Markdown to the tree every output renders — `inkletter/md_to_ast.py`.

import MarkdownIt from 'markdown-it';
import {
  Attributes,
  BlankLine,
  BlockCode,
  BlockHtml,
  BlockQuote,
  BlockText,
  CodeSpan,
  Document,
  Emphasis,
  Hashtag,
  Heading,
  Image,
  ImageLink,
  InlineHtml,
  LineBreak,
  Link,
  List,
  ListItem,
  LiteralText,
  MailLink,
  Mention,
  type Node,
  Paragraph,
  SoftBreak,
  StrikeThrough,
  Strong,
  Table,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  TaskListItem,
  TelLink,
  ThematicBreak,
  UrlLink,
} from './ast.js';
import {
  bareLinksPlugin,
  hashtagPlugin,
  linkAttributesPlugin,
  taskListsPlugin,
  typedListsPlugin,
} from './plugins/index.js';
import type { ImageAttributes } from './plugins/link_attributes.js';
import { quote, strip } from './stdlib.js';
import { SyntaxTreeNode } from './syntax_tree.js';
import { DEFAULT_THEME, type Theme } from './theme.js';
import { Annotation } from './visitors/annotation.js';
import { BlockTextMerger } from './visitors/merger.js';
import { Trimmer } from './visitors/trimmer.js';
import type { URLFactory } from './shortener.js';
import { URLRewriter } from './visitors/urls.js';

// What a link's target keeps as it is: the delimiters of a URL (RFC 3986)
// and the octets already encoded; anything else — a space, an accented
// letter — is percent-encoded.
const URL_SAFE = ":/?#@!$&()*+,;=%";

// What a node of an image's alt reads as, when it is not its own text.
const ALT_SPELLINGS: Readonly<Record<string, string>> = { softbreak: ' ', hardbreak: ' ', html_inline: '' };

// The containers whose blocks may have blank lines between them — and whose
// last block, not the container, says where it ends.
const CONTAINERS = ['root', 'blockquote', 'bullet_list', 'ordered_list', 'list_item'];

type Built = Node | Node[];
type Build = (node: SyntaxTreeNode) => Built;
type LinkKind = new (text: Node[], href: string, title: string | null) => Link;

/** Turns markdown-it's tree into Inkletter's.
 *
 *  One method per kind of markdown-it node, named after it: each says what
 *  the node becomes, and calls `build` on what it holds. What the parser
 *  reads is markdown-it's business, and what a node means the passes'
 *  after this one: here, only shapes change. */
export class ASTBuilder {
  // The target's scheme says what a link is: the node each one becomes, and
  // a plain link for the rest — addresses, relative paths, whatever else.
  static readonly LINKS_BY_SCHEME: Readonly<Record<string, LinkKind>> = { urn: Mention, mailto: MailLink, tel: TelLink };
  // what a scheme names is a class of its own; anything else is an address
  static readonly DEFAULT_LINK: LinkKind = UrlLink;

  // the document's lines: the blank ones it ends on are counted too
  constructor(private readonly lineCount: number) {}

  /** What the node becomes: a node, or several where a container of
   *  markdown-it's is none of Inkletter's (a table's body, a line of text). */
  build(node: SyntaxTreeNode): Built {
    const method = (this as unknown as Record<string, Build | undefined>)[node.type];
    if (!method) throw new Error(`no node for markdown-it's ${node.type}`);
    return method.call(this, node);
  }

  built(nodes: SyntaxTreeNode[]): Node[] {
    return nodes.flatMap((node) => this.build(node));
  }

  // --- Blank lines ---

  /** The line after a block's last: a container ends with what it holds —
   *  markdown-it counts in a list the blank lines that follow it, which are
   *  the document's. */
  static endOf(node: SyntaxTreeNode): number {
    const last = node.children.at(-1);
    if (CONTAINERS.includes(node.type) && last) return ASTBuilder.endOf(last);
    if (node.type === 'list_item') return node.map[0] + 1;
    return node.map[1];
  }

  /** A container's blocks, with the blank lines its author left between
   *  them: from the line it starts on to the one it ends on, when known. */
  blocks(children: SyntaxTreeNode[], start: number, end: number | null = null): Node[] {
    const nodes: Node[] = [];
    let line = start;
    for (const child of children) {
      if (child.map[0] > line) nodes.push(new BlankLine(child.map[0] - line));
      nodes.push(...this.built([child]));
      line = ASTBuilder.endOf(child);
    }
    if (end !== null && end > line) nodes.push(new BlankLine(end - line));
    return nodes;
  }

  // --- Blocks ---

  root(node: SyntaxTreeNode): Document {
    return new Document(this.blocks(node.children, 0, this.lineCount));
  }

  paragraph(node: SyntaxTreeNode): Paragraph | BlockText {
    const children = this.built(node.children);
    // a tight list's item holds its text, not a paragraph
    return node.hidden ? new BlockText(children) : new Paragraph(children);
  }

  heading(node: SyntaxTreeNode): Heading {
    return new Heading(Number(node.tag.slice(1)), this.built(node.children));
  }

  blockquote(node: SyntaxTreeNode): BlockQuote {
    return new BlockQuote(this.blocks(node.children, node.map[0]));
  }

  fence(node: SyntaxTreeNode): BlockCode {
    return new BlockCode(node.content, strip(node.info) || null);
  }

  code_block(node: SyntaxTreeNode): BlockCode {
    // indented code ends on its last line, its line breaks aside
    return new BlockCode(node.content.replace(/\n+$/, ''), null);
  }

  html_block(node: SyntaxTreeNode): BlockHtml {
    return new BlockHtml(node.content.replace(/^\n+|\n+$/g, ''));
  }

  hr(): ThematicBreak {
    return new ThematicBreak();
  }

  // --- Lists ---

  bullet_list(node: SyntaxTreeNode): List {
    return new List(this.items(node), false);
  }

  ordered_list(node: SyntaxTreeNode): List {
    const start = node.attr('start');
    return new List(this.items(node), true, start === null ? null : Number(start));
  }

  items(node: SyntaxTreeNode): (ListItem | TaskListItem)[] {
    return this.built(node.children).filter((item) => item instanceof ListItem || item instanceof TaskListItem);
  }

  list_item(node: SyntaxTreeNode): ListItem | TaskListItem {
    const children = this.blocks(node.children, node.map[0]);
    const checked = node.meta.checked;
    return typeof checked === 'boolean' ? new TaskListItem(children, checked) : new ListItem(children);
  }

  // --- Tables ---

  table(node: SyntaxTreeNode): Table {
    const [header, ...rows] = this.built(node.children);
    return new Table(
      header instanceof TableHeader ? header : null,
      rows.filter((row) => row instanceof TableRow),
    );
  }

  thead(node: SyntaxTreeNode): TableHeader {
    const [row] = node.children;
    return new TableHeader(row ? this.built(row.children).filter((cell) => cell instanceof TableHeaderCell) : []);
  }

  tbody(node: SyntaxTreeNode): Node[] {
    return this.built(node.children);
  }

  tr(node: SyntaxTreeNode): TableRow {
    return new TableRow(this.built(node.children).filter((cell) => cell instanceof TableCell));
  }

  th(node: SyntaxTreeNode): TableHeaderCell {
    return new TableHeaderCell(this.built(node.children), ASTBuilder.alignOf(node));
  }

  td(node: SyntaxTreeNode): TableCell {
    return new TableCell(this.built(node.children), ASTBuilder.alignOf(node));
  }

  static alignOf(node: SyntaxTreeNode): string | null {
    return (node.attr('style') ?? '').replace(/^text-align:/, '') || null;
  }

  // --- Inline ---

  inline(node: SyntaxTreeNode): Node[] {
    return this.built(node.children);
  }

  text(node: SyntaxTreeNode): Node[] {
    // markdown-it leaves an empty text where a mark's delimiters were
    return node.content ? [new LiteralText(node.content)] : [];
  }

  text_special(node: SyntaxTreeNode): LiteralText {
    // an escaped character or an entity, read: in an image's alt, which the
    // parser does not join to the text around it
    return new LiteralText(node.content);
  }

  hashtag(node: SyntaxTreeNode): Hashtag {
    return new Hashtag(String(node.meta.name));
  }

  em(node: SyntaxTreeNode): Emphasis {
    return new Emphasis(this.built(node.children));
  }

  strong(node: SyntaxTreeNode): Strong {
    return new Strong(this.built(node.children));
  }

  s(node: SyntaxTreeNode): StrikeThrough {
    return new StrikeThrough(this.built(node.children));
  }

  code_inline(node: SyntaxTreeNode): CodeSpan {
    return new CodeSpan(node.content);
  }

  html_inline(node: SyntaxTreeNode): InlineHtml {
    return new InlineHtml(node.content);
  }

  softbreak(): SoftBreak {
    return new SoftBreak();
  }

  hardbreak(): LineBreak {
    return new LineBreak();
  }

  link(node: SyntaxTreeNode): Node {
    const url = node.attr('href') ?? '';
    const title = node.attr('title');
    const text = this.built(node.children);
    // What the target's scheme names — an entity, for a URN — becomes its
    // own node here, once, rather than being recognised again by every
    // visitor that walks past a link.
    const kind = ASTBuilder.LINKS_BY_SCHEME[Link.schemeOf(url)];
    if (kind) return new kind(text, url, title);
    // A link holding an image is the image, clickable: the rest of its
    // label is dropped
    const image = text.find((child) => child instanceof Image);
    if (image) return new ImageLink(image, url, title);
    return new ASTBuilder.DEFAULT_LINK(text, url, title);
  }

  image(node: SyntaxTreeNode): Image {
    const attributes = (node.meta.ink_attributes ?? {}) as ImageAttributes;
    return new Image(
      node.attr('src') ?? '',
      ASTBuilder.altText(node.children),
      node.attr('title'),
      new Attributes(attributes.width ?? null, attributes.height ?? null, attributes.align ?? null),
    );
  }

  /** What an image's alt reads as: its words, its code and its tags as
   *  written, a break as a space, its marks gone — an HTML alt holds no
   *  markup. */
  static altText(nodes: SyntaxTreeNode[]): string {
    return nodes.map((node) => ASTBuilder.altPart(node)).join('');
  }

  static altPart(node: SyntaxTreeNode): string {
    const spelling = ALT_SPELLINGS[node.type];
    if (spelling !== undefined) return spelling;
    if (node.type === 'hashtag') return `#${String(node.meta.name)}`;
    if (['text', 'text_special', 'code_inline'].includes(node.type)) return node.content;
    return ASTBuilder.altText(node.children);
  }
}

/** The parser: CommonMark, GitHub's tables and strikethrough, and what
 *  Inkletter reads beyond them. */
export function createMarkdown(linkAttributes = true): MarkdownIt {
  const markdown = MarkdownIt('commonmark').enable(['table', 'strikethrough']);
  // A target is kept as written, whatever its scheme: what a link to
  // `javascript:` becomes is each output's to decide, and a URN must reach
  // the mention it names.
  markdown.validateLink = acceptAnyLink;
  markdown.normalizeLink = normalizeLink;
  markdown.normalizeLinkText = String;
  markdown.use(hashtagPlugin);
  // A bare address is text to CommonMark, and a link to every reader: read
  // as one, so the URL factory shortens it and the counter charges it like
  // any other.
  markdown.use(bareLinksPlugin);
  markdown.use(taskListsPlugin);
  // A list ends where its author stopped writing it: a line written after
  // an item, without a marker, is its own block.
  markdown.use(typedListsPlugin);
  if (linkAttributes) markdown.use(linkAttributesPlugin);
  return markdown;
}

function acceptAnyLink(): boolean {
  return true;
}

/** A link's target as the document holds it: written as typed, its
 *  entities and escapes already read, the rest percent-encoded. */
function normalizeLink(url: string): string {
  return quote(url, URL_SAFE);
}

/** How many lines markdown-it reads in a text: a last newline closes the
 *  last line rather than opening one. */
export function lineCount(text: string): number {
  const normalized = text.replace(/\r\n?/g, '\n');
  if (!normalized) return 0;
  return (normalized.match(/\n/g)?.length ?? 0) + (normalized.endsWith('\n') ? 0 : 1);
}

/** The document as parsed, before any pass has said what it means. */
export function readMarkdown(markdownText: string, linkAttributes = true): Document {
  const tokens = createMarkdown(linkAttributes).parse(markdownText, {});
  return new ASTBuilder(lineCount(markdownText)).root(new SyntaxTreeNode(tokens));
}

export interface AstOptions {
  boldLinkIsButton?: boolean;
  linkAttributes?: boolean;
  theme?: Theme | null;
  urlFactory?: URLFactory | null;
}

export function parseMarkdownToAst(markdownText: string, options: AstOptions = {}): Document {
  const { boldLinkIsButton = true, linkAttributes = true, theme = null, urlFactory = null } = options;
  const ast = readMarkdown(markdownText, linkAttributes);
  // what is laid out on one line — a label, a name, a cell — is one
  new Trimmer().visit(ast);
  new BlockTextMerger(boldLinkIsButton).visit(ast);
  new Annotation(theme ?? DEFAULT_THEME, linkAttributes).visit(ast);
  // Last, once every node says what it is: the factory is offered a
  // button's URL as a button's.
  if (urlFactory !== null) new URLRewriter(urlFactory).visit(ast);
  return ast;
}
