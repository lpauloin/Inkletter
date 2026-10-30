// The base of every pass and every output — `inkletter/visitors/generic.py`:
// a `visit_<Kind>` method per node kind it handles, `genericVisit` for the
// rest.

import type { Node } from '../ast.js';
import { ScopeStack } from './scope.js';

type VisitMethod = (node: Node, scope: ScopeStack) => void;

export class NodeVisitor {
  scope = new ScopeStack();

  /** Dispatch to the node's `visit_<Kind>`, or to `genericVisit`. */
  visit(node: Node, scope: ScopeStack = this.scope): void {
    const method = (this as unknown as Record<string, VisitMethod | undefined>)[`visit_${node.kind}`];
    if (method) method.call(this, node, scope);
    else this.genericVisit(node, scope);
  }

  genericVisit(node: Node, scope: ScopeStack): void {
    for (const child of node.getChildren()) this.visit(child, scope);
  }
}
