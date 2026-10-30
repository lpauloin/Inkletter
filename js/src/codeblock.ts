// Code as nested blocks of text, resolved to a string — `inkletter/codeblock.py`.
// The MJML, the text and the post all write through it.

import { codePoints, lstrip, rstrip, splitLines, strip } from './stdlib.js';

const INDENT_SIZE = 2; // spaces per indent level
const NEWLINE = '\n';

/** One more prefix on every line that follows, until the matching Dedent:
 *  the indentation spaces by default, but a quote's `> ` just as well. */
export class Indent {
  constructor(public prefix: string | null = null) {}
}

export class Dedent {}

export class Newline {}

/** A run of text, what it costs where cost is counted, and what it is to
 *  whoever reads the output: `cost` is null for text that costs its own
 *  characters; `kind` and `display` say what the run is and what a reader
 *  is shown of it — a mention's name rather than its marker — `display`
 *  being the text itself unless said otherwise. */
export class TextElement {
  readonly display: string;

  constructor(
    public text: string,
    public indented = true,
    public cost: number | null = null,
    public kind: SegmentKind = 'text',
    display: string | null = null,
  ) {
    this.display = display ?? text;
  }
}

/** What one fragment of a line is to its reader. */
export type SegmentKind = 'text' | 'mention' | 'hashtag' | 'link';

/** One fragment of a resolved line: what it is, what a reader is shown,
 *  what it costs. */
export interface Segment {
  readonly kind: SegmentKind;
  readonly display: string;
  readonly cost: number;
}

/** A resolved line: as it goes out, what it costs, fragment by fragment. */
export interface Line {
  readonly text: string;
  readonly cost: number;
  readonly segments: readonly Segment[];
}

export type CodeElement = Indent | Dedent | Newline | TextElement | CodeBlock;

export class CodeBlock {
  elements: CodeElement[] = [];

  addIndent(prefix: string | null = null): void {
    this.elements.push(new Indent(prefix));
  }

  addDedent(): void {
    this.elements.push(new Dedent());
  }

  addText(
    text: string,
    indented = true,
    cost: number | null = null,
    kind: SegmentKind = 'text',
    display: string | null = null,
  ): void {
    this.elements.push(new TextElement(text, indented, cost, kind, display));
  }

  addNewline(): void {
    this.elements.push(new Newline());
  }

  addCodeblock(block: CodeBlock): void {
    this.elements.push(block);
  }
}

/** Resolves a block to text, and weighs it on the way: every line costs its
 *  prefixes, its fragments — what they declared, or `measure` of what they
 *  say — and the break that ends it. Trailing whitespace goes from every
 *  line, from plain text only. */
export class CodeBlockResolver {
  private readonly indent: string;
  private prefixes: string[] = [];
  private lines: Line[] = [];
  private parts: TextElement[] | null = null;

  constructor(
    indentSize = INDENT_SIZE,
    private readonly startingIndent = 0,
    private readonly measure: (text: string) => number = codePoints,
  ) {
    this.indent = ' '.repeat(indentSize);
    this.reset();
  }

  reset(): void {
    this.prefixes = Array.from({ length: this.startingIndent }, () => this.indent);
    this.lines = [];
    this.parts = null;
  }

  accept(element: CodeElement): void {
    if (element instanceof Indent) this.prefixes.push(element.prefix ?? this.indent);
    else if (element instanceof Dedent) this.dedent();
    else if (element instanceof Newline) this.newline();
    else if (element instanceof TextElement) this.text(element);
    else for (const child of element.elements) this.accept(child);
  }

  private dedent(): void {
    if (this.prefixes.length <= this.startingIndent) throw new Error('Cannot dedent below zero');
    this.prefixes.pop();
  }

  private newline(): void {
    this.parts ??= [new TextElement(this.prefixes.join(''))];
    this.closeLine();
  }

  private text(node: TextElement): void {
    this.parts ??= [new TextElement(node.indented ? this.prefixes.join('') : '')];
    this.parts.push(node);
  }

  private closeLine(): void {
    const parts = this.parts ?? [];
    for (let last = parts.at(-1); last && last.cost === null && !rstrip(last.text); last = parts.at(-1)) parts.pop();
    const last = parts.at(-1);
    if (last && last.cost === null) {
      parts[parts.length - 1] = new TextElement(rstrip(last.text), true, null, last.kind, rstrip(last.display));
    }
    this.lines.push({
      text: parts.map((part) => part.text).join(''),
      cost: parts.reduce((sum, part) => sum + this.costOf(part), 0),
      segments: parts
        .filter((part) => part.display)
        .map((part) => ({ kind: part.kind, display: part.display, cost: this.costOf(part) })),
    });
    this.parts = null;
  }

  private costOf(part: TextElement): number {
    return part.cost ?? this.measure(part.text);
  }

  resolve(block: CodeBlock): string {
    this.reset();
    this.accept(block);
    if (this.parts !== null) this.closeLine();
    return this.lines.map((line) => line.text).join(NEWLINE);
  }

  /** The resolved lines, the blank ones they end on gone — the lines of
   *  `rstrip(resolve(...))`. */
  get writtenLines(): Line[] {
    const lines = [...this.lines];
    while (lines.length && !lines.at(-1)?.text) lines.pop();
    return lines;
  }

  /** What the resolved text weighs once its trailing blank lines are gone —
   *  the weight of `rstrip(resolve(...))`. */
  get length(): number {
    const lines = this.writtenLines;
    return lines.reduce((sum, line) => sum + line.cost, 0) + Math.max(lines.length - 1, 0);
  }
}

export function codeblockFromString(content: string, indentSize = 2): CodeBlock {
  const block = new CodeBlock();
  let level = 0;
  for (const line of splitLines(content.replace(/^\n+|\n+$/g, ''))) {
    const raw = rstrip(line);
    const lineLevel = Math.floor((line.length - lstrip(line).length) / indentSize);
    for (; level < lineLevel; level += 1) block.addIndent();
    for (; level > lineLevel; level -= 1) block.addDedent();
    if (strip(raw) === '') block.addNewline();
    else {
      block.addText(lstrip(raw));
      block.addNewline();
    }
  }
  for (; level > 0; level -= 1) block.addDedent();
  return block;
}
