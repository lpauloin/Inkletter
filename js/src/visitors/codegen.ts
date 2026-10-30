// Emits MJML from the annotated tree — `inkletter/visitors/codegen.py`.
// Every styling decision reaches it as annotation-provided instructions: no
// theme in sight.

import {
  type BlockCode,
  type BlockHtml,
  type BlockQuote,
  BlockText,
  type Button,
  type CodeSpan,
  type Document,
  type Emphasis,
  type Hashtag,
  type HeadAnnotation,
  type Heading,
  type Image,
  type ImageLink,
  type ImageRow,
  type InlineHtml,
  type Link,
  type List,
  type ListItem,
  type LiteralText,
  type MediaObject,
  type Node,
  type Paragraph,
  type StrikeThrough,
  type Strong,
  type Table,
  type TableCell,
  type TableHeader,
  type TableRow,
  type TaskListItem,
  type ThematicBreak,
} from '../ast.js';
import { CodeBlock, CodeBlockResolver, TextElement } from '../codeblock.js';
import { htmlEscape, splitLines } from '../stdlib.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';

type Attrs = Readonly<Record<string, string | number>>;

interface TagOptions {
  selfClosing?: boolean;
  inline?: boolean;
}

export class Codegen extends NodeVisitor {
  root = new CodeBlock();
  resolver = new CodeBlockResolver();
  current = this.root;

  getCode(): string {
    return this.resolver.resolve(this.root);
  }

  /** `<name …>`, what `body` writes, then `</name>` — on lines of their own
   *  unless inline. */
  blockTag(name: string, attrs: Attrs | null, options: TagOptions, body: () => void = () => {}): void {
    const { selfClosing = false, inline = false } = options;
    const attrsText = Object.entries(attrs ?? {})
      .map(([key, value]) => ` ${key}="${htmlEscape(String(value), true)}"`)
      .join('');
    if (selfClosing) {
      this.current.addText(`<${name}${attrsText}/>`);
      if (!inline) this.current.addNewline();
      body();
      return;
    }
    const parent = this.current;
    const block = new CodeBlock();
    if (!inline && parent.elements.at(-1) instanceof TextElement) block.addNewline();
    block.addText(`<${name}${attrsText}>`);
    if (!inline) {
      block.addNewline();
      block.addIndent();
    }
    parent.addCodeblock(block);
    this.current = block;
    body();
    this.current = parent;
    if (!inline) {
      if (block.elements.at(-1) instanceof TextElement) block.addNewline();
      this.current.addDedent();
    }
    this.current.addText(`</${name}>`);
    if (!inline) this.current.addNewline();
  }

  ensureOpenText(node: Node, body: () => void, inline = false): void {
    if (node.annotations.requires_text) {
      this.blockTag('mj-text', (node.annotations.text_attrs as Attrs | undefined) ?? null, { inline }, body);
    } else body();
  }

  visit_Document(node: Document, scope: ScopeStack): void {
    this.blockTag('mjml', null, {}, () => {
      const head = node.head;
      if (head) this.emitHead(head);
      this.blockTag('mj-body', node.annotations.body_attrs as Attrs, {}, () => this.emitBands(node.children, scope));
    });
  }

  static definesOwnColumns(node: Node): boolean {
    return Boolean(node.annotations.defines_own_columns);
  }

  /** The document body alternates two kinds of bands: blocks that stack in a
   *  single column share one flow section, while nodes defining their own
   *  column layout emit their own mj-section through their visitor. */
  emitBands(children: Node[], scope: ScopeStack): void {
    let band: Node[] = [];
    const flush = () => {
      if (band.length) this.emitFlowBand(band, scope);
      band = [];
    };
    for (const child of children) {
      if (Codegen.definesOwnColumns(child)) {
        flush();
        this.visit(child, scope);
      } else band.push(child);
    }
    flush();
  }

  emitFlowBand(children: Node[], scope: ScopeStack): void {
    this.blockTag('mj-section', null, {}, () =>
      this.blockTag('mj-column', null, {}, () => {
        for (const child of children) this.visit(child, scope);
      }),
    );
  }

  visit_Button(node: Button, scope: ScopeStack): void {
    const attrs: Record<string, string> = { href: node.href };
    if (node.title) attrs.title = node.title;
    this.blockTag('mj-button', attrs, { inline: true }, () => this.genericVisit(node, scope));
    this.current.addNewline();
  }

  visit_ImageRow(node: ImageRow, scope: ScopeStack): void {
    this.blockTag('mj-section', null, {}, () => {
      for (const image of node.children) this.blockTag('mj-column', null, {}, () => this.visit(image, scope));
    });
  }

  visit_MediaObject(node: MediaObject, scope: ScopeStack): void {
    // the Annotation pass decided the layout and all its parameters
    if (node.annotations.media_layout === 'stacked') this.emitMediaStacked(node, scope);
    else this.emitMediaColumns(node, scope);
  }

  emitMediaStacked(node: MediaObject, scope: ScopeStack): void {
    this.blockTag('mj-section', null, {}, () =>
      this.blockTag('mj-column', null, {}, () => {
        this.visit(node.image, scope);
        for (const child of node.children) this.visit(child, scope);
      }),
    );
  }

  emitMediaColumns(node: MediaObject, scope: ScopeStack): void {
    const [imageWidth = '', textWidth = ''] = node.annotations.media_widths as readonly string[];
    const direction = node.annotations.media_direction;
    const attrs: Record<string, string> = typeof direction === 'string' && direction ? { direction } : {};
    this.blockTag('mj-section', attrs, {}, () => {
      this.blockTag('mj-column', { width: imageWidth }, {}, () => this.visit(node.image, scope));
      this.blockTag('mj-column', { width: textWidth }, {}, () => {
        for (const child of node.children) this.visit(child, scope);
      });
    });
  }

  emitHead(head: HeadAnnotation): void {
    this.blockTag('mj-head', null, {}, () => {
      if (head.title) {
        const title = head.title;
        this.blockTag('mj-title', null, { inline: true }, () => this.current.addText(htmlEscape(title, false)));
        this.current.addNewline();
      }
      for (const [name, href] of head.fonts) this.blockTag('mj-font', { name, href }, { selfClosing: true });
      this.blockTag('mj-attributes', null, {}, () => {
        for (const [tag, attrs] of Object.entries(head.attributes)) this.blockTag(tag, attrs, { selfClosing: true });
      });
      this.blockTag('mj-style', { inline: 'inline' }, {}, () => this.addRawLines(head.css));
    });
  }

  visit_Paragraph(node: Paragraph, scope: ScopeStack): void {
    if (node.annotations.requires_paragraph_tag) {
      this.blockTag('p', null, { inline: true }, () => this.genericVisit(node, scope));
    } else this.genericVisit(node, scope);
  }

  visit_Heading(node: Heading, scope: ScopeStack): void {
    this.ensureOpenText(node, () =>
      this.blockTag(`h${node.level}`, null, { inline: true }, () => this.genericVisit(node, scope)),
    );
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    this.ensureOpenText(node, () => this.genericVisit(node, scope));
  }

  visit_BlockQuote(node: BlockQuote, scope: ScopeStack): void {
    this.ensureOpenText(node, () => this.blockTag('blockquote', null, {}, () => this.genericVisit(node, scope)));
  }

  visit_BlockCode(node: BlockCode): void {
    this.ensureOpenText(node, () =>
      this.blockTag('pre', null, {}, () => this.current.addText(htmlEscape(node.code), false)),
    );
  }

  visit_ThematicBreak(node: ThematicBreak): void {
    this.blockTag('mj-divider', node.annotations.divider_attrs as Attrs, { selfClosing: true });
  }

  visit_LineBreak(): void {
    this.current.addText('<br/>');
    this.current.addNewline();
  }

  visit_SoftBreak(): void {
    // Deliberate divergence from CommonMark (which renders a soft break as a
    // space): newsletter authors line-wrap on purpose.
    this.current.addText('<br/>');
    this.current.addNewline();
  }

  visit_BlankLine(): void {}

  visit_Image(node: Image): void {
    // an alt always, empty for an image that says nothing
    const attrs: Record<string, string> = { src: node.url, alt: node.altText };
    if (node.title) attrs.title = node.title;
    let tag: string;
    if (node.annotations.requires_manual_image) {
      tag = 'img';
      attrs.style = String(node.annotations.image_style);
    } else {
      tag = 'mj-image';
      const padding = node.annotations.image_padding;
      if (typeof padding === 'string' && padding) attrs.padding = padding;
      Object.assign(attrs, (node.annotations.image_size as Attrs | undefined) ?? {});
    }
    this.blockTag(tag, attrs, { selfClosing: true });
  }

  visit_ImageLink(node: ImageLink): void {
    const img = node.img;
    if (img.annotations.requires_manual_image) {
      // href is not a valid <img> attribute: wrap in an anchor
      const linkAttrs: Record<string, string> = { href: node.href };
      if (node.title) linkAttrs.title = node.title;
      this.blockTag('a', linkAttrs, { inline: true }, () => {
        const imgAttrs: Record<string, string> = { src: img.url, alt: img.altText };
        if (img.title) imgAttrs.title = img.title;
        imgAttrs.style = String(img.annotations.image_style);
        this.blockTag('img', imgAttrs, { selfClosing: true, inline: true });
      });
      return;
    }
    const attrs: Record<string, string> = { src: img.url, href: node.href, alt: img.altText };
    if (img.title) attrs.title = img.title;
    const padding = node.annotations.image_padding;
    if (typeof padding === 'string' && padding) attrs.padding = padding;
    Object.assign(attrs, (img.annotations.image_size as Attrs | undefined) ?? {});
    this.blockTag('mj-image', attrs, { selfClosing: true, inline: true });
  }

  visit_List(node: List, scope: ScopeStack): void {
    this.ensureOpenText(node, () => {
      const attrs: Record<string, number> = {};
      if (node.ordered && node.start !== null && node.start !== 1) attrs.start = node.start;
      this.blockTag(node.ordered ? 'ol' : 'ul', attrs, {}, () => this.genericVisit(node, scope));
    });
  }

  visit_ListItem(node: ListItem, scope: ScopeStack): void {
    this.blockTag('li', null, {}, () => this.genericVisit(node, scope));
  }

  visit_TaskListItem(node: TaskListItem, scope: ScopeStack): void {
    const checkbox = node.checked ? '☑' : '☐';
    // the checkbox replaces the bullet for this item only, so mixed
    // task/normal lists keep their bullets on normal items
    this.blockTag('li', { style: 'list-style-type: none;' }, {}, () => {
      const [block, ...extra] = node.children;
      if (!(block instanceof BlockText)) throw new Error('a task item opens on its text');
      this.current.addText(`${checkbox} `);
      for (const child of block.getChildren()) this.visit(child, scope);
      this.current.addNewline();
      for (const child of extra) this.visit(child, scope);
    });
  }

  visit_Table(node: Table, scope: ScopeStack): void {
    this.blockTag(node.annotations.requires_manual_table ? 'table' : 'mj-table', null, {}, () => {
      if (node.header) this.visit(node.header, scope);
      for (const row of node.rows) this.visit(row, scope);
    });
  }

  visit_TableHeader(node: TableHeader, scope: ScopeStack): void {
    this.blockTag('tr', null, {}, () => {
      for (const head of node.headers) this.visit(head, scope);
    });
  }

  visit_TableRow(node: TableRow, scope: ScopeStack): void {
    this.blockTag('tr', null, {}, () => {
      for (const cell of node.row) this.visit(cell, scope);
    });
  }

  visit_TableHeaderCell(node: TableCell, scope: ScopeStack): void {
    this.cell('th', node, scope);
  }

  visit_TableCell(node: TableCell, scope: ScopeStack): void {
    this.cell('td', node, scope);
  }

  cell(tag: string, node: TableCell, scope: ScopeStack): void {
    const attrs: Record<string, string> = node.align ? { align: node.align } : {};
    attrs.style = String(node.annotations.cell_style);
    this.blockTag(tag, attrs, { inline: true }, () => this.genericVisit(node, scope));
    this.current.addNewline();
  }

  visit_LiteralText(node: LiteralText): void {
    this.ensureOpenText(node, () => this.current.addText(htmlEscape(node.value, false)));
  }

  visit_Emphasis(node: Emphasis, scope: ScopeStack): void {
    this.ensureOpenText(node, () => this.blockTag('em', null, { inline: true }, () => this.genericVisit(node, scope)));
  }

  visit_Strong(node: Strong, scope: ScopeStack): void {
    this.ensureOpenText(node, () =>
      this.blockTag('strong', null, { inline: true }, () => this.genericVisit(node, scope)),
    );
  }

  visit_StrikeThrough(node: StrikeThrough, scope: ScopeStack): void {
    this.ensureOpenText(node, () => this.blockTag('del', null, { inline: true }, () => this.genericVisit(node, scope)));
  }

  visit_UrlLink(node: Link, scope: ScopeStack): void {
    this.anchor(node, scope);
  }

  visit_MailLink(node: Link, scope: ScopeStack): void {
    this.anchor(node, scope);
  }

  visit_TelLink(node: Link, scope: ScopeStack): void {
    this.anchor(node, scope);
  }

  anchor(node: Link, scope: ScopeStack): void {
    this.ensureOpenText(node, () => {
      const attrs: Record<string, string> = { href: node.href };
      if (node.title) attrs.title = node.title;
      this.blockTag('a', attrs, { inline: true }, () => this.genericVisit(node, scope));
    });
  }

  visit_InlineHtml(node: InlineHtml): void {
    this.ensureOpenText(node, () => this.current.addText(node.value));
  }

  /** Verbatim content, wrapped in mj-raw when it sits at flow level. */
  emitRaw(node: Node, value: string): void {
    if (node.annotations.requires_raw) this.blockTag('mj-raw', null, {}, () => this.addRawLines(value));
    else this.addRawLines(value);
  }

  visit_BlockHtml(node: BlockHtml): void {
    this.emitRaw(node, node.value);
  }

  addRawLines(value: string): void {
    for (const line of splitLines(value)) {
      this.current.addText(line);
      this.current.addNewline();
    }
  }

  visit_Hashtag(node: Hashtag): void {
    this.ensureOpenText(node, () => {
      const style = node.annotations.hashtag_style;
      if (typeof style === 'string' && style) {
        this.blockTag('span', { style }, { inline: true }, () => this.current.addText(`#${node.name}`));
      } else this.current.addText(`#${node.name}`);
    });
  }

  visit_CodeSpan(node: CodeSpan): void {
    this.ensureOpenText(node, () =>
      this.blockTag('code', null, { inline: true }, () => this.current.addText(htmlEscape(node.code))),
    );
  }
}
