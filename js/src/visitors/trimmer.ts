// Puts on one line what every output lays out on one line —
// `inkletter/visitors/trimmer.py`. A link's label, a mention's name: right
// after parsing, a break inside one of them becomes a space and the
// whitespace at either end goes, on the tree, once. A table cell needs
// none: the parser trims it, and it holds no break.

import { BlockNode, InlineHtml, LineBreak, LiteralText, type Node, SoftBreak } from '../ast.js';
import { lstrip, rstrip, strip } from '../stdlib.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';

export class Trimmer extends NodeVisitor {
  visit_UrlLink(node: BlockNode, scope: ScopeStack): void {
    this.trim(node, scope);
  }

  visit_MailLink(node: BlockNode, scope: ScopeStack): void {
    this.trim(node, scope);
  }

  visit_TelLink(node: BlockNode, scope: ScopeStack): void {
    this.trim(node, scope);
  }

  visit_Mention(node: BlockNode, scope: ScopeStack): void {
    this.trim(node, scope);
  }

  /** Flatten this node's run, then go on. */
  trim(node: BlockNode, scope: ScopeStack): void {
    Trimmer.flatten(node);
    this.genericVisit(node, scope);
  }

  static flatten(node: BlockNode): void {
    Trimmer.unbreak(node);
    Trimmer.trimEdge(node, true);
    Trimmer.trimEdge(node, false);
  }

  /** The whitespace at one end of the run goes, under its marks too and past
   *  a hand-written tag, up to the first word. */
  static trimEdge(node: BlockNode, leading: boolean): void {
    const children = node.children;
    let at = leading ? 0 : children.length - 1;
    const step = leading ? 1 : -1;
    while (at >= 0 && at < children.length) {
      const child = children[at];
      if (child instanceof InlineHtml) {
        at += step;
        continue;
      }
      if (Trimmer.blank(child)) {
        children.splice(at, 1);
        if (!leading) at -= 1;
        continue;
      }
      if (child instanceof LiteralText) child.value = leading ? lstrip(child.value) : rstrip(child.value);
      else if (child instanceof BlockNode) Trimmer.trimEdge(child, leading);
      return;
    }
  }

  /** Every break in the run a space, under its marks too. */
  static unbreak(node: BlockNode): void {
    node.children = node.children.map((child) =>
      child instanceof SoftBreak || child instanceof LineBreak ? new LiteralText(' ') : child,
    );
    for (const child of node.children) if (child instanceof BlockNode) Trimmer.unbreak(child);
  }

  static blank(node: Node | undefined): boolean {
    return node instanceof LiteralText && !strip(node.value);
  }
}
