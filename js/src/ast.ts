// The tree every output is rendered from — `inkletter/ast.py`, node for node.
//
// A visitor dispatches on `kind`, the class's own name: the bundler that
// minifies a class name leaves a string alone.

import { strip, urlSplit } from './stdlib.js';

export type Annotations = Record<string, AnnotationValue>;
// What a pass may write on a node for the passes after it.
export type AnnotationValue =
  | string
  | boolean
  | null
  | ReadonlySet<string>
  | readonly string[]
  | Readonly<Record<string, string>>
  | HeadAnnotation;

export interface HeadAnnotation {
  attributes: Record<string, Record<string, string>>;
  css: string;
  fonts: readonly (readonly [string, string])[];
  title: string | null;
}

export abstract class Node {
  abstract readonly kind: string;
  annotations: Annotations = {};

  getChildren(): Node[] {
    return [];
  }

  /** Nothing to read: a break, or text made of whitespace. */
  isBlank(): boolean {
    return false;
  }
}

export abstract class BlockNode extends Node {
  children: Node[];

  constructor(children: Node[] | Node | null) {
    super();
    this.children = children === null ? [] : Array.isArray(children) ? children : [children];
  }

  override getChildren(): Node[] {
    return this.children;
  }
}

// --- Text elements ---

export abstract class Text extends Node {}

export abstract class TextBlock extends BlockNode {}

/** What Python reads as `isinstance(node, Text)`: a text element, or a
 *  mark wrapping some — `TextBlock` is both a text and a block there. */
export function isText(node: Node): boolean {
  return node instanceof Text || node instanceof TextBlock;
}

export class LiteralText extends Text {
  readonly kind = 'LiteralText';

  constructor(public value: string) {
    super();
  }

  override isBlank(): boolean {
    return !strip(this.value);
  }
}

export class CodeSpan extends Text {
  readonly kind = 'CodeSpan';

  constructor(public code: string) {
    super();
  }
}

/** A `#tag` in the text: `#` at the start of a word, then letters, digits
 *  or underscores, one letter at least — so `#2026` is a number and `C#` a
 *  language, and a `# ` with its space is a heading long before the text is
 *  read. Its own node, read before any mark inside it could be one:
 *  `#équipe_rh` is one tag, not a name with an italic in it. The name is
 *  kept without the `#`, which each rendering writes. */
export class Hashtag extends Text {
  readonly kind = 'Hashtag';

  constructor(public name: string) {
    super();
  }
}

export class InlineHtml extends Text {
  readonly kind = 'InlineHtml';

  constructor(public value: string) {
    super();
  }
}

export class Emphasis extends TextBlock {
  readonly kind = 'Emphasis';
}

export class Strong extends TextBlock {
  readonly kind = 'Strong';

  /** The one link this bold wraps, blanks aside — the call to action,
   *  which a lone bold link is — and null when it wraps anything else.
   *  A mention does not qualify: it names someone, it asks nothing. */
  get ask(): Link | null {
    const inner = this.children.filter((child) => !child.isBlank());
    const [only] = inner;
    if (inner.length === 1 && only instanceof Link && !(only instanceof Mention)) return only;
    return null;
  }
}

export class StrikeThrough extends TextBlock {
  readonly kind = 'StrikeThrough';
}

/** What a link is, whatever it points at: a label, a target, a title.
 *  Never a node of the tree itself — a target's scheme says which of the
 *  classes below it is, and a visitor names the one it renders. */
export abstract class Link extends TextBlock {
  constructor(
    text: Node[] | Node | null,
    public href: string,
    public title: string | null = null,
  ) {
    super(text);
  }

  /** The scheme a target starts with, lower-cased — `https`, `mailto`,
   *  `urn` — and `""` for a path relative to nothing, or for a target the
   *  standard splitter refuses: what it is not, at least, is an address. */
  static schemeOf(target: string): string {
    return urlSplit(target)?.scheme ?? '';
  }

  // Each kind says its scheme; only an address has to read it off its
  // target, which may be `http`, `https` or none at all.
  abstract get scheme(): string;
}

/** An address — `http`, `https`, or a path relative to one — that a reader
 *  follows and a factory may shorten. */
export class UrlLink extends Link {
  readonly kind = 'UrlLink';

  get scheme(): string {
    // read off the href each time: a factory may rewrite it
    return Link.schemeOf(this.href);
  }
}

/** Someone named in the text, with the entity's URN as its target. A link
 *  by nature, and its own class so that each rendering says what it does
 *  with one, and so that a URL factory, which is shown addresses alone,
 *  never replaces the URN with a dead one. The children carry the name as
 *  it is to be displayed, with no leading marker. */
export class Mention extends Link {
  readonly kind = 'Mention';

  get scheme(): string {
    return 'urn';
  }

  get urn(): string {
    return this.href;
  }
}

/** `mailto:` — an address to write to. */
export class MailLink extends Link {
  readonly kind = 'MailLink';

  get scheme(): string {
    return 'mailto';
  }

  get address(): string {
    return urlSplit(this.href)?.path ?? '';
  }
}

/** `tel:` — a number to call, shown as such where nothing can dial. */
export class TelLink extends Link {
  readonly kind = 'TelLink';

  get scheme(): string {
    return 'tel';
  }

  get number(): string {
    return urlSplit(this.href)?.path ?? '';
  }
}

// --- Block elements ---

export class Document extends BlockNode {
  readonly kind = 'Document';

  /** What the annotation pass wrote for the mail's head. */
  get head(): HeadAnnotation | null {
    const head = this.annotations.head;
    return typeof head === 'object' && head !== null && 'fonts' in head ? (head as HeadAnnotation) : null;
  }
}

export class Paragraph extends BlockNode {
  readonly kind = 'Paragraph';
}

export class Heading extends BlockNode {
  readonly kind = 'Heading';

  constructor(
    public level: number,
    text: Node[] | Node | null,
  ) {
    super(text);
  }
}

export class BlockText extends BlockNode {
  readonly kind = 'BlockText';
}

export class BlockQuote extends BlockNode {
  readonly kind = 'BlockQuote';
}

export class BlockCode extends Node {
  readonly kind = 'BlockCode';

  constructor(
    public code: string,
    public language: string | null = null,
  ) {
    super();
  }
}

export class BlockHtml extends Node {
  readonly kind = 'BlockHtml';

  constructor(public value: string) {
    super();
  }
}

// --- Image element ---

/** What the author wrote in braces after an image: facts about the asset,
 *  never appearance. Not a child of the image — it describes it — so no
 *  visitor ever walks into it. */
export class Attributes {
  constructor(
    public width: string | null = null,
    public height: string | null = null,
    public align: string | null = null,
  ) {}

  get isSet(): boolean {
    return Boolean(this.width || this.height || this.align);
  }
}

export class Image extends Node {
  readonly kind = 'Image';
  attributes: Attributes;

  constructor(
    public url: string,
    // what the image says to whoever cannot see it: text alone, an HTML alt
    // holding no markup
    public altText = '',
    public title: string | null = null,
    attributes: Attributes | null = null,
  ) {
    super();
    this.attributes = attributes ?? new Attributes();
  }

  get scheme(): string {
    return Link.schemeOf(this.url);
  }
}

export class ImageLink extends Node {
  readonly kind = 'ImageLink';

  constructor(
    public img: Image,
    public href: string,
    public title: string | null = null,
  ) {
    super();
  }

  get scheme(): string {
    return Link.schemeOf(this.href);
  }

  override getChildren(): Node[] {
    return [this.img];
  }
}

/** A paragraph made only of images: rendered as side-by-side columns. */
export class ImageRow extends BlockNode {
  readonly kind = 'ImageRow';
}

/** A paragraph made only of a bold link: a call-to-action button. */
export class Button extends BlockNode {
  readonly kind = 'Button';

  constructor(
    children: Node[],
    public href: string,
    public title: string | null = null,
  ) {
    super(children);
  }

  get scheme(): string {
    return Link.schemeOf(this.href);
  }
}

/** A paragraph opening (or closing) with a single image beside its text. */
export class MediaObject extends BlockNode {
  readonly kind = 'MediaObject';

  constructor(
    public image: Image | ImageLink,
    children: Node[],
    public side: 'left' | 'right' = 'left',
  ) {
    super(children);
  }

  override getChildren(): Node[] {
    return [this.image, ...this.children];
  }
}

// --- Terminal elements ---

export abstract class TextTerminal extends Text {
  override isBlank(): boolean {
    return true;
  }
}

export abstract class Terminal extends Node {}

export class ThematicBreak extends Terminal {
  readonly kind = 'ThematicBreak';
}

export class LineBreak extends TextTerminal {
  readonly kind = 'LineBreak';
}

export class SoftBreak extends TextTerminal {
  readonly kind = 'SoftBreak';
}

/** The lines an author left between two blocks. Markdown reads them as one
 *  break and keeps the count for an output that does: a post goes out as
 *  it was typed. */
export class BlankLine extends Terminal {
  readonly kind = 'BlankLine';

  constructor(public lines = 1) {
    super();
  }
}

// --- List elements ---

export class List extends Node {
  readonly kind = 'List';

  constructor(
    public elements: (ListItem | TaskListItem)[],
    public ordered = false,
    public start: number | null = null,
  ) {
    super();
  }

  override getChildren(): Node[] {
    return this.elements;
  }
}

export class ListItem extends BlockNode {
  readonly kind = 'ListItem';
}

export class TaskListItem extends BlockNode {
  readonly kind = 'TaskListItem';

  constructor(
    children: Node[],
    public checked = false,
  ) {
    super(children);
  }
}

// --- Table elements ---

export class Table extends Node {
  readonly kind = 'Table';

  constructor(
    public header: TableHeader | null = null,
    public rows: TableRow[] = [],
  ) {
    super();
  }

  override getChildren(): Node[] {
    return [...(this.header ? [this.header] : []), ...this.rows];
  }
}

export class TableRow extends Node {
  readonly kind = 'TableRow';

  constructor(public row: TableCell[]) {
    super();
  }

  override getChildren(): Node[] {
    return this.row;
  }
}

export class TableCell extends BlockNode {
  readonly kind: string = 'TableCell';

  constructor(
    cell: Node[],
    public align: string | null = null,
  ) {
    super(cell);
  }
}

export class TableHeaderCell extends TableCell {
  override readonly kind = 'TableHeaderCell';
}

export class TableHeader extends Node {
  readonly kind = 'TableHeader';

  constructor(public headers: TableHeaderCell[]) {
    super();
  }

  override getChildren(): Node[] {
    return this.headers;
  }
}
