// Groups each run of inline nodes of a paragraph or a heading into a
// BlockText, and promotes the paragraphs a layout convention names: an image
// row, an image beside its text, a button — `inkletter/visitors/merger.py`.

import {
  type BlockNode,
  BlockText,
  Button,
  type Document,
  Image,
  ImageLink,
  ImageRow,
  isText,
  LiteralText,
  MediaObject,
  type Node,
  Paragraph,
  Strong,
  TextTerminal,
} from '../ast.js';
import { lstrip, rstrip } from '../stdlib.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';

export class BlockTextMerger extends NodeVisitor {
  constructor(private readonly boldLinkIsButton = true) {
    super();
  }

  static mergeInlineSequences(children: Node[]): Node[] {
    const merged: Node[] = [];
    const buffer: Node[] = [];
    for (const child of children) {
      if (isText(child)) {
        buffer.push(child);
        continue;
      }
      BlockTextMerger.flush(buffer, merged);
      merged.push(child);
    }
    BlockTextMerger.flush(buffer, merged);
    // the breaks a paragraph opens or ends on separate nothing
    while (merged[0] instanceof TextTerminal) merged.shift();
    while (merged.at(-1) instanceof TextTerminal) merged.pop();
    return merged;
  }

  /** The run gathered so far as a BlockText, the breaks at its edges beside
   *  it — an image on a line of its own keeps the breaks around it, one
   *  inside a line has none. */
  static flush(buffer: Node[], merged: Node[]): void {
    const leading: Node[] = [];
    const trailing: Node[] = [];
    while (buffer[0] instanceof TextTerminal) leading.push(buffer.shift()!);
    while (buffer.at(-1) instanceof TextTerminal) trailing.unshift(buffer.pop()!);
    merged.push(...leading);
    if (buffer.length) merged.push(new BlockText([...buffer]));
    buffer.length = 0;
    merged.push(...trailing);
  }

  processBlocknode(node: BlockNode, scope: ScopeStack): void {
    node.children = BlockTextMerger.mergeInlineSequences(node.children);
    for (const child of node.children) this.visit(child, scope);
  }

  visit_Paragraph(node: BlockNode, scope: ScopeStack): void {
    this.processBlocknode(node, scope);
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    // a tight item's line: the breaks it opens or ends on separate nothing
    while (node.children[0] instanceof TextTerminal) node.children.shift();
    while (node.children.at(-1) instanceof TextTerminal) node.children.pop();
    this.genericVisit(node, scope);
  }

  visit_Heading(node: BlockNode, scope: ScopeStack): void {
    this.processBlocknode(node, scope);
  }

  // An image announces itself to the paragraph asking what it holds
  // (`promoteButton`): pushed on the scope, the one place kinds are recorded.

  visit_Image(node: Image, scope: ScopeStack): void {
    scope.push(node);
    scope.pop(node);
  }

  visit_ImageLink(node: ImageLink, scope: ScopeStack): void {
    scope.push(node);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Document(node: Document, scope: ScopeStack): void {
    scope.push(node);
    const promoted: Node[] = [];
    for (const child of node.children) {
      // record afresh: each child is promoted on what it holds
      scope.recordTypes();
      this.visit(child, scope);
      promoted.push(...this.promoteParagraph(child, scope.types()));
    }
    node.children = promoted;
    scope.pop(node);
  }

  /** Turn image-only paragraphs into ImageRow(s) and image-beside-text
   *  paragraphs into MediaObject (top-level layout conventions). */
  promoteParagraph(node: Node, types: ReadonlySet<string>): Node[] {
    if (!(node instanceof Paragraph)) return [node];
    const images = node.children.filter((child) => child instanceof Image || child instanceof ImageLink);
    const others = node.children.filter((child) => !(child instanceof Image || child instanceof ImageLink));
    if (!images.length) {
      if (this.boldLinkIsButton) {
        const button = BlockTextMerger.promoteButton(node, types);
        if (button !== null) return [button];
      }
      return [node];
    }

    if (others.every((child) => BlockTextMerger.isBlank(child))) {
      if (images.length === 1) {
        // drop the blank filler around a lone image
        node.children = images;
        return [node];
      }
      // up to 4 images stay on one row, more wrap into rows of 3
      if (images.length <= 4) return [new ImageRow(images)];
      const rows: Node[] = [];
      for (let at = 0; at < images.length; at += 3) rows.push(new ImageRow(images.slice(at, at + 3)));
      return rows;
    }

    const [image] = images;
    if (images.length === 1 && image) {
      if (node.children[0] === image) {
        BlockTextMerger.stripEdge(others, true);
        return [new MediaObject(image, others, 'left')];
      }
      if (node.children.at(-1) === image) {
        BlockTextMerger.stripEdge(others, false);
        return [new MediaObject(image, others, 'right')];
      }
    }
    return [node];
  }

  /** A paragraph made only of a bold link becomes a Button (CTA). */
  static promoteButton(node: Paragraph, types: ReadonlySet<string>): Button | null {
    const blocks = node.children.filter((child) => !BlockTextMerger.isBlank(child));
    const [block] = blocks;
    if (blocks.length !== 1 || !(block instanceof BlockText)) return null;
    const inlines = block.children.filter((child) => !child.isBlank());
    const [strong] = inlines;
    if (inlines.length !== 1 || !(strong instanceof Strong)) return null;
    const link = strong.ask;
    if (link === null) return null;
    // never a button on an image link: the image always wins, even nested
    // deep inside the label
    if (types.has('Image') || types.has('ImageLink')) return null;
    return new Button(link.children, link.href, link.title);
  }

  /** A break between two of a paragraph's pieces, or text of spaces. */
  static isBlank(node: Node): boolean {
    if (node instanceof TextTerminal) return true;
    return node instanceof BlockText && node.children.every((child) => child.isBlank());
  }

  /** Trim the breaks and the whitespace left over next to the extracted
   *  image. */
  static stripEdge(blocks: Node[], leading: boolean): void {
    while ((leading ? blocks[0] : blocks.at(-1)) instanceof TextTerminal) {
      if (leading) blocks.shift();
      else blocks.pop();
    }
    const block = leading ? blocks[0] : blocks.at(-1);
    if (!(block instanceof BlockText) || !block.children.length) return;
    const text = leading ? block.children[0] : block.children.at(-1);
    if (text instanceof LiteralText) text.value = leading ? lstrip(text.value) : rstrip(text.value);
  }
}
