// The context a visitor carries as it walks down the tree —
// `inkletter/visitors/scope.py`.
//
// A value set on a scope is visible to everything below it and dies with
// it, which covers the inherited flags (in_text, is_in_button…). Two ways
// round the one-way street, when a scope needs to know about its own
// subtree: `recordTypes`, for what node types live below, and an ordinary
// mutable value that descendants fill in.

import type { Node } from '../ast.js';

const TYPES = 'node_types';

// a flag, a style set, or a collector the scope above owns and the nodes below fill
export type ScopeValue = string | boolean | null | object;

interface Frame {
  node: Node;
  values: Map<string, ScopeValue>;
}

export class ScopeStack {
  stack: Frame[] = [];

  push(node: Node): void {
    this.stack.push({ node, values: new Map() });
    // every node announces its type to whoever is recording below
    for (const frame of [...this.stack].reverse()) {
      const types = frame.values.get(TYPES);
      if (types instanceof Set) {
        types.add(node.kind);
        return;
      }
    }
  }

  pop(node: Node): Frame {
    const top = this.stack.pop();
    if (!top) throw new Error('Scope underflow');
    if (top.node !== node) throw new Error(`Scope mismatch: expected ${top.node.kind}, got ${node.kind}`);
    return top;
  }

  set(key: string, value: ScopeValue): void {
    const top = this.stack.at(-1);
    if (!top) throw new Error('No active scope');
    top.values.set(key, value);
  }

  get<T extends ScopeValue>(key: string): T | undefined {
    for (let at = this.stack.length - 1; at >= 0; at -= 1) {
      const values = this.stack[at]?.values;
      if (values?.has(key)) return values.get(key) as T;
    }
    return undefined;
  }

  /** Record the node kinds living under this scope: lets a scope ask
   *  "what am I made of?" without walking its own subtree — and as a
   *  whitelist: a kind nobody thought about shows up in the set. */
  recordTypes(): void {
    this.set(TYPES, new Set<string>());
  }

  types(): ReadonlySet<string> {
    return this.get<Set<string>>(TYPES) ?? new Set();
  }
}
