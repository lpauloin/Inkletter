// markdown-it's flat tokens as a tree — what `markdown_it.tree.SyntaxTreeNode`
// gives the Python package, which markdown-it does not ship in JavaScript.
// An opening and its closing token become one node holding what is between
// them; an inline token, or an image, holds its own children.

import type { Token } from 'markdown-it';

export class SyntaxTreeNode {
  /** `paragraph` for `paragraph_open`, `root` for the document. */
  readonly type: string;
  readonly children: SyntaxTreeNode[];
  // the token that says what the node is: the opening one of a pair
  private readonly token: Token | null;

  constructor(tokens: Token[], token: Token | null = null) {
    this.token = token;
    this.type = token === null ? 'root' : token.nesting === 1 ? token.type.replace(/_open$/, '') : token.type;
    this.children = nest(tokens);
  }

  get map(): [number, number] {
    const map = this.token?.map;
    if (!map) throw new Error(`a ${this.type} has no line map`);
    return [map[0], map[1]];
  }

  get tag(): string {
    return this.token?.tag ?? '';
  }

  get content(): string {
    return this.token?.content ?? '';
  }

  get info(): string {
    return this.token?.info ?? '';
  }

  get hidden(): boolean {
    return this.token?.hidden ?? false;
  }

  get meta(): Record<string, unknown> {
    return (this.token?.meta as Record<string, unknown> | null) ?? {};
  }

  attr(name: string): string | null {
    return this.token?.attrGet(name) ?? null;
  }
}

function nest(tokens: Token[]): SyntaxTreeNode[] {
  const nodes: SyntaxTreeNode[] = [];
  for (let at = 0; at < tokens.length; at += 1) {
    const token = tokens[at];
    if (!token) break;
    if (token.nesting !== 1) {
      nodes.push(new SyntaxTreeNode(token.children ?? [], token));
      continue;
    }
    let depth = 1;
    let close = at + 1;
    for (; close < tokens.length && depth > 0; close += 1) depth += tokens[close]?.nesting ?? 0;
    nodes.push(new SyntaxTreeNode(tokens.slice(at + 1, close - 1), token));
    at = close - 1;
  }
  return nodes;
}
