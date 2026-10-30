// Puts on one line what every output lays out on one line —
// `inkletter/visitors/trimmer.py`. A link's label, a mention's name: right
// after parsing, a break inside one of them becomes a space and the
// whitespace at either end goes, on the tree, once. A table cell needs
// none: the parser trims it, and it holds no break.

import { type BlockNode, LineBreak, LiteralText, type Node, SoftBreak } from '../ast.js';
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
    const children = node.children.map((child) =>
      child instanceof SoftBreak || child instanceof LineBreak ? new LiteralText(' ') : child,
    );
    while (children.length && Trimmer.blank(children[0])) children.shift();
    while (children.length && Trimmer.blank(children.at(-1))) children.pop();
    const first = children[0];
    if (first instanceof LiteralText) first.value = lstrip(first.value);
    const last = children.at(-1);
    if (last instanceof LiteralText) last.value = rstrip(last.value);
    node.children = children;
  }

  static blank(node: Node | undefined): boolean {
    return node instanceof LiteralText && !strip(node.value);
  }
}
