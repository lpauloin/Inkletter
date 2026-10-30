// Renders the normalized tree as a LinkedIn post —
// `inkletter/visitors/linkedingen.py`. The plain-text output, with a feed's
// choices, and the price: every fragment it writes carries what the
// platform will count for it, fixed when the fragment is written and summed
// by the resolver as it lays the lines out.

import {
  BlankLine,
  CodeSpan,
  type Document,
  type Hashtag,
  type Heading,
  type Image,
  type ImageLink,
  type InlineHtml,
  Link,
  LiteralText,
  type MailLink,
  type MediaObject,
  type Mention,
  type Node,
  type Annotations,
  type Table,
  type TelLink,
  type UrlLink,
} from '../ast.js';
import { CodeBlockResolver, type Line, type SegmentKind } from '../codeblock.js';
import { costOfLink, costOfMention, costOfText } from '../counting.js';
import { isBareDomain, isSpelledBy } from '../plugins/bare_domains.js';
import { rstrip, strip, unquote } from '../stdlib.js';
import type { ScopeStack } from './scope.js';
import { TextCodegen } from './textgen.js';

const BULLET = '• ';
const CELL_SEPARATOR = ' — ';
const LABEL_SEPARATOR = ' : ';

// The delimiters of the mention marker, for which nothing documents an
// escape: a name carrying either goes out as plain text.
const MARKER_DELIMITERS = ['|', ']'];

// Unicode look-alikes for the three styles the platform does not have —
// text, not formatting, and opt-in.
//
// | Styles in force  | Letters become                           |
// |------------------|------------------------------------------|
// | bold             | 𝗺𝗼𝘁 sans-serif bold                       |
// | italic           | 𝘮𝘰𝘵 sans-serif italic                     |
// | bold and italic  | 𝙢𝙤𝙩 sans-serif bold italic               |
// | strikethrough    | a combining stroke after each letter,    |
// |                  | digit, sign or space — never an emoji    |
//
// Only unaccented ASCII letters have a look-alike.
const ASCII_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';

function lookalikes(lower: number, upper: number): ReadonlyMap<string, string> {
  const targets = [...Array.from({ length: 26 }, (_, at) => lower + at), ...Array.from({ length: 26 }, (_, at) => upper + at)];
  return new Map([...ASCII_LETTERS].map((letter, at) => [letter, String.fromCodePoint(targets[at] ?? 0)]));
}

const LETTERS: Readonly<Record<string, ReadonlyMap<string, string>>> = {
  bold: lookalikes(0x1d5ee, 0x1d5d4),
  italic: lookalikes(0x1d622, 0x1d608),
  'bold italic': lookalikes(0x1d656, 0x1d63c),
};
const STRIKE = '\u0336';
// What the stroke goes after: letters, digits, punctuation, spaces and the
// like. Not an emoji, nor what an emoji is built of.
const STRUCK = /^[\p{L}\p{N}\p{P}\p{Zs}\p{Sc}\p{Sm}]$/u;
const SPACE_SEPARATOR = /^\p{Zs}$/u;

/** A stroke after each character it goes after — and not on a space that
 *  touches something it skips. */
function strike(text: string): string {
  const chars = Array.from(text);
  return chars
    .map((char, at) => {
      let struck = STRUCK.test(char);
      if (struck && SPACE_SEPARATOR.test(char)) {
        struck = [chars[at - 1], chars[at + 1]].every((neighbour) => neighbour === undefined || STRUCK.test(neighbour));
      }
      return struck ? char + STRIKE : char;
    })
    .join('');
}

/** `text` in the look-alikes of `styles`. */
function substitute(text: string, styles: ReadonlySet<string>): string {
  const key = ['bold', 'italic'].filter((style) => styles.has(style)).join(' ');
  const letters = LETTERS[key];
  let styled = letters ? Array.from(text, (char) => letters.get(char) ?? char).join('') : text;
  if (styles.has('strikethrough')) styled = strike(styled);
  return styled;
}

/** A post as the platform will take it, and as a feed shows it. */
export class LinkedinRender {
  constructor(
    /** The text that goes out. */
    readonly text: string,
    /** What the platform counts for it, in UTF-16 code units. */
    readonly length: number,
    /** Its lines, each fragment saying what the feed shows of it — a
     *  mention's name, an address as written — and what it costs. */
    readonly lines: readonly Line[],
    /** Bold, italic or strikethrough written that the feed will not show —
     *  never when look-alikes stand in. */
    readonly unrenderedFormatting: boolean,
    /** A heading written: the feed shows none, look-alikes or not. */
    readonly unrenderedHeadings: boolean,
  ) {}

  /** The post as the feed shows it, on one string: what a quote of it reads
   *  like to a human — never the marker that carries a mention. */
  get shownText(): string {
    return this.lines.map((line) => line.segments.map((segment) => segment.display).join('')).join('\n');
  }
}

export class LinkedinCodegen extends TextCodegen {
  /** What a node reads as, with no rendering. */
  static plainText(node: Node): string {
    if (node instanceof LiteralText) return node.value;
    if (node instanceof CodeSpan) return node.code;
    return node.getChildren().map((child) => LinkedinCodegen.plainText(child)).join('');
  }

  override resolver = new CodeBlockResolver(2, 0, costOfText);
  // what was written that the feed will not show
  styledWords = false;
  headings = false;

  constructor(
    private readonly unicodeStyling = false,
    private readonly linkLength: number | null = null,
  ) {
    super(BULLET);
  }

  /** Text costs what it says, unless it is priced — a marker, an address —
   *  and shows what it says, unless it is a marker or an address the author
   *  wrote otherwise. */
  override write(text: string, cost: number | null = null, kind: SegmentKind = 'text', display: string | null = null): void {
    this.current.addText(text, true, cost, kind, display);
  }

  /** The author's words, in the look-alikes of the styles in force, when
   *  substitutes are wanted. Only words: a marker or an address never. */
  writeStyled(text: string, annotations: Annotations): void {
    const styles = annotations.styles instanceof Set && annotations.styles.size ? annotations.styles : null;
    if (styles && strip(text)) this.styledWords = true;
    if (this.unicodeStyling && styles) this.write(substitute(text, styles));
    else this.write(text);
  }

  /** The address in full, priced at the short link it will become; the feed
   *  shows it as a reader reads it, its letters decoded — as the author
   *  wrote it, when that is the same address. */
  writeLink(url: string, written: string | null = null): void {
    const readable = unquote(url);
    const display = written !== null && isSpelledBy(readable, written) ? written : readable;
    this.write(url, costOfLink(url, this.linkLength), 'link', display);
  }

  /** The post, and what the platform will count for it. */
  render(document: Document): LinkedinRender {
    this.visit(document);
    const text = rstrip(this.resolver.resolve(this.root));
    return new LinkedinRender(
      text,
      this.resolver.length,
      this.resolver.writtenLines,
      this.styledWords && !this.unicodeStyling,
      this.headings,
    );
  }

  // --- Blocks ---

  /** Blocks separated by the blank lines their author left: the BlankLine
   *  between two blocks is the separation itself, and the lines a document
   *  opens or ends on separate nothing. */
  override emitBlocks(nodes: Node[], scope: ScopeStack): void {
    let written = false;
    let blank = 0;
    for (const node of nodes) {
      if (node instanceof BlankLine) {
        blank = Math.max(blank, node.lines);
        continue;
      }
      const block = this.renderBlock(node, scope);
      if (!block.elements.length) continue;
      if (written) for (let line = 0; line < blank; line += 1) this.line();
      this.current.addCodeblock(block);
      written = true;
      blank = 0;
    }
  }

  /** The text on its line, and no underline. */
  override visit_Heading(node: Heading, scope: ScopeStack): void {
    this.headings = true;
    this.genericVisit(node, scope);
    this.closeLine();
  }

  override visit_ThematicBreak(): void {} // forty dashes across a feed are noise; the blank line stays

  /** One line per row, cells joined by a dash. */
  override visit_Table(node: Table, scope: ScopeStack): void {
    const rows = [...(node.header ? [node.header.headers] : []), ...node.rows.map((row) => row.row)];
    for (const row of rows) {
      row
        .filter((cell) => cell.children.length)
        .forEach((cell, index) => {
          if (index) this.write(CELL_SEPARATOR);
          this.genericVisit(cell, scope);
        });
      this.closeLine();
    }
  }

  // --- Inline ---

  override visit_InlineHtml(node: InlineHtml): void {
    // the tags vanish — except a closing anchor, which spells out its address
    const href = node.annotations.anchor_href;
    if (typeof href === 'string' && href) {
      this.write(LABEL_SEPARATOR);
      this.writeLink(href);
    }
  }

  /** `@[<urn>|<name>]`, weighed at the name alone; a name the marker cannot
   *  carry goes out as plain text. */
  visit_Mention(node: Mention): void {
    const name = LinkedinCodegen.plainText(node);
    if (MARKER_DELIMITERS.some((delimiter) => name.includes(delimiter))) {
      this.write(`@${name}`);
      return;
    }
    this.write(`@[${node.urn}|${name}]`, costOfMention(name), 'mention', name);
  }

  /** `label : url`, and the url alone when the label is one too. */
  override visit_UrlLink(node: UrlLink, scope: ScopeStack): void {
    const label = LinkedinCodegen.plainText(node);
    if (label && label !== node.href && !LinkedinCodegen.isAnAddress(label)) {
      this.genericVisit(node, scope);
      this.write(LABEL_SEPARATOR);
    }
    this.writeLink(node.href, label);
  }

  static isAnAddress(label: string): boolean {
    return ['http', 'https'].includes(Link.schemeOf(label)) || isBareDomain(label);
  }

  override visit_MailLink(node: MailLink, scope: ScopeStack): void {
    this.named(node, node.address, scope);
  }

  override visit_TelLink(node: TelLink, scope: ScopeStack): void {
    this.named(node, node.number, scope);
  }

  /** `label : target`, and the target alone when the label is it. */
  override named(node: Link, target: string, scope: ScopeStack): void {
    const label = LinkedinCodegen.plainText(node);
    if (label && label !== target && label !== node.href) {
      this.genericVisit(node, scope);
      this.write(LABEL_SEPARATOR);
    }
    this.write(target);
  }

  override visit_LiteralText(node: LiteralText): void {
    this.writeStyled(node.value, node.annotations);
  }

  override visit_Hashtag(node: Hashtag): void {
    // as written, whatever style is in force
    this.write(`#${node.name}`, null, 'hashtag');
  }

  override visit_CodeSpan(node: CodeSpan): void {
    this.writeStyled(node.code, node.annotations);
  }

  // --- Images are not supported: written, they stay as written ---

  override visit_Image(node: Image): void {
    this.write(`![${node.altText}](${node.url})`);
  }

  override visit_ImageLink(node: ImageLink): void {
    this.write(`[![${node.img.altText}](${node.img.url})](${node.href})`);
    this.closeLine();
  }

  override visit_MediaObject(node: MediaObject, scope: ScopeStack): void {
    // the image beside its text, written as one paragraph: one blank line
    // between them as in every output
    super.emitBlocks([node.image, ...node.children], scope);
  }
}
