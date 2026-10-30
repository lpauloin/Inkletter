// Decorates the tree with everything the codegen needs to render each node —
// `inkletter/visitors/annotation.py`. All styling lives here, the codegen
// only executes. There is always a theme.

import {
  BlockCode,
  BlockHtml,
  BlockQuote,
  BlockText,
  Button,
  CodeSpan,
  Document,
  Emphasis,
  Hashtag,
  Heading,
  Image,
  ImageLink,
  ImageRow,
  InlineHtml,
  LineBreak,
  Link,
  type MailLink,
  List,
  ListItem,
  LiteralText,
  MediaObject,
  Mention,
  type Node,
  Paragraph,
  SoftBreak,
  TextTerminal,
  StrikeThrough,
  Strong,
  Table,
  TableCell,
  TableHeaderCell,
  type TelLink,
  TaskListItem,
  ThematicBreak,
  type UrlLink,
  runsSomething,
} from '../ast.js';
import { isBareDomain } from '../plugins/bare_domains.js';
import { strip } from '../stdlib.js';
import { splitMediaRatio, type Theme } from '../theme.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';

/** The href of a hand-written opening anchor: what the outputs that cannot
 *  pass the tag through — text, post, fragment — spell or rebuild. */
export const ANCHOR_HREF = /^<a\s[^>]*\bhref\s*=\s*["']([^"']*)["']/i;

/** Whether a label is an address already — with its scheme, or a domain
 *  written without one — rather than a name for one. */
function isAnAddress(label: string): boolean {
  return ['http', 'https'].includes(Link.schemeOf(label)) || isBareDomain(label);
}

export class Annotation extends NodeVisitor {
  constructor(
    private readonly theme: Theme,
    private readonly linkAttributes = true,
  ) {
    super();
  }

  visit_Document(node: Document, scope: ScopeStack): void {
    scope.push(node);
    // an empty slot the first h1 fills in, with its text or with null when
    // it turns out not to be usable as a title
    const slot: (string | null)[] = [];
    scope.set('document_title', slot);
    // what the document writes that a feed will not show: the styles on its
    // words, look-alikes or not, and its headings
    scope.set('document', node);
    const written = new Set<string>();
    scope.set('styles_written', written);
    node.annotations.has_headings = false;
    const theme = this.theme;
    const imageAttrs: Record<string, string> = { align: theme.images.align };
    if (!this.linkAttributes) {
      // without link attributes no image carries a width of its own: each
      // takes the full width of a phone's screen
      imageAttrs['fluid-on-mobile'] = 'true';
    }
    if (!['0', '0px'].includes(theme.images.border_radius)) imageAttrs['border-radius'] = theme.images.border_radius;
    node.annotations.head = {
      // mj-table and mj-button have their own MJML defaults and must follow
      // the theme instead
      attributes: {
        'mj-section': {
          padding: theme.layout.section_padding,
          'background-color': theme.layout.content_background_color,
        },
        'mj-text': {
          'font-family': theme.text.font_family,
          'font-size': theme.text.font_size,
          'line-height': theme.text.line_height,
          color: theme.text.color,
        },
        'mj-table': {
          color: theme.text.color,
          'font-family': theme.text.font_family,
          'font-size': theme.text.font_size,
          'line-height': theme.text.line_height,
        },
        'mj-button': {
          'background-color': theme.buttonBackground(),
          color: theme.buttons.color,
          'border-radius': theme.buttons.border_radius,
          'font-weight': theme.buttons.font_weight,
          'inner-padding': theme.buttons.padding,
          align: theme.buttons.align,
          'font-family': theme.text.font_family,
          'font-size': theme.text.font_size,
        },
        'mj-image': imageAttrs,
      },
      css: theme.toCss(),
      fonts: theme.fonts,
      title: null,
    };
    node.annotations.body_attrs = {
      width: theme.layout.width,
      'background-color': theme.layout.background_color,
    };
    this.genericVisit(node, scope);
    node.annotations.head.title = slot[0] ?? null;
    node.annotations.styles_written = written;
    scope.pop(node);
  }

  /** Bold, italic, strikethrough: the styles in force below, carried down to
   *  every text they cover. */
  addStyle(scope: ScopeStack, style: string): void {
    scope.set('styles', new Set([...(scope.get<ReadonlySet<string>>('styles') ?? []), style]));
  }

  markStyles(node: Node, scope: ScopeStack, text: string): void {
    // a mention's name is never dressed: it is what the platform matches
    const styles = scope.get<ReadonlySet<string>>('styles');
    if (styles?.size && !scope.get('is_in_mention') && !scope.get('is_in_address')) {
      node.annotations.styles = styles;
      // spaces alone wear no style a reader could miss
      if (strip(text)) for (const style of styles) scope.get<Set<string>>('styles_written')!.add(style);
    }
  }

  /** Whether a node sits in raw HTML already — an mj-text's content, a
   *  table, a list item, a button's label — where no MJML component may
   *  open. */
  static inRawHtml(scope: ScopeStack): boolean {
    return Boolean(
      scope.get('in_text') || scope.get('is_in_table') || scope.get('is_in_list_item') || scope.get('is_in_button'),
    );
  }

  markTextIfNeeded(node: Node, scope: ScopeStack): void {
    if (!Annotation.inRawHtml(scope)) {
      node.annotations.requires_text = true;
      scope.set('in_text', true);
    }
  }

  markManualTableIfNeeded(node: Node, scope: ScopeStack): void {
    // in raw HTML — a list, a quote, a cell — an mj-table is an unknown tag
    if (Annotation.inRawHtml(scope)) node.annotations.requires_manual_table = true;
  }

  /** Fold what the author asked for into the render instructions: the theme
   *  decides how images look, the document only says how wide this one is,
   *  and where it sits. */
  applyAuthorAttributes(node: Image): void {
    const attributes = node.attributes;
    if (!attributes.isSet) return;
    if (node.annotations.requires_manual_image) {
      const sizes = (
        [
          ['width', attributes.width],
          ['height', attributes.height],
        ] as const
      )
        .filter(([, value]) => value)
        .map(([name, value]) => `${name}: ${value};`);
      if (sizes.length) node.annotations.image_style = `${String(node.annotations.image_style)} ${sizes.join(' ')}`;
      return;
    }
    const size: Record<string, string> = {};
    for (const [name, value] of [
      ['width', attributes.width],
      ['height', attributes.height],
      ['align', attributes.align],
    ] as const) {
      if (value) size[name] = value;
    }
    node.annotations.image_size = size;
  }

  markManualImageIfNeeded(node: Node, scope: ScopeStack): void {
    // In raw HTML an mj-image would leak as an unknown tag: render a plain
    // <img> instead, with its style ready to emit.
    if (Annotation.inRawHtml(scope)) {
      node.annotations.requires_manual_image = true;
      let style = 'max-width: 100%; height: auto;';
      const radius = this.theme.images.border_radius;
      if (!['0', '0px'].includes(radius)) style += ` border-radius: ${radius};`;
      node.annotations.image_style = style;
    }
  }

  visit_List(node: List, scope: ScopeStack): void {
    scope.push(node);
    scope.set('is_in_list', true);
    this.markTextIfNeeded(node, scope);
    // an ordered list numbers its items from its start, a box included, as
    // a reader of the mail counts them — a rank is a matter between siblings
    if (node.ordered) {
      const start = node.start ?? 1;
      node.elements.forEach((item, offset) => {
        item.annotations.number = start + offset;
      });
    }
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_TaskListItem(node: TaskListItem, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    // the box opens the item's first line, drawn by whoever writes it
    const [first] = node.children;
    if (first) first.annotations.checkbox = node.checked ? '☑' : '☐';
    scope.set('is_in_list_item', true);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_ListItem(node: ListItem, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    scope.set('is_in_list_item', true);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Paragraph(node: Paragraph, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    // At flow level each paragraph gets its own mj-text, and the padding
    // between them separates them. Inside a raw-HTML context — a quote, a
    // list item, a cell — the paragraph must carry its own tag.
    node.annotations.requires_paragraph_tag = Annotation.inRawHtml(scope);
    if (!node.annotations.requires_paragraph_tag) {
      // At flow level an image is a block of its own, stacked between the
      // lines around it: the breaks beside it separate what the mail
      // already sets apart.
      for (const child of node.children) if (child instanceof TextTerminal) child.annotations.between_blocks = true;
    }
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    Annotation.markTheAsks(node);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_BlockQuote(node: BlockQuote, scope: ScopeStack): void {
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_BlockCode(node: BlockCode, scope: ScopeStack): void {
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Table(node: Table, scope: ScopeStack): void {
    scope.push(node);
    this.markManualTableIfNeeded(node, scope);
    scope.set('is_in_table', true);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_TableHeaderCell(node: TableHeaderCell, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    const table = this.theme.table;
    let style = `border-bottom: 2px solid ${table.border_color}; padding: ${table.cell_padding};`;
    if (table.header_color) style += ` color: ${table.header_color};`;
    if (table.header_background_color) style += ` background-color: ${table.header_background_color};`;
    if (!node.align) style += ' text-align: left;';
    node.annotations.cell_style = style;
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_TableCell(node: TableCell, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    const table = this.theme.table;
    node.annotations.cell_style = `border-bottom: 1px solid ${table.border_color}; padding: ${table.cell_padding};`;
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Button(node: Button, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    // The one link of the document that is the ask, said in the node for
    // whoever handles URLs after this pass.
    node.annotations.button = true;
    // The label is a raw-HTML-inline context: no MJML component inside.
    scope.set('is_in_button', true);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_ImageRow(node: ImageRow, scope: ScopeStack): void {
    scope.push(node);
    // A row defines its own column layout: it emits its own mj-section. Each
    // image carries the row spacing to apply.
    node.annotations.defines_own_columns = true;
    const gap = this.theme.images.row_gap;
    for (const image of node.children) image.annotations.image_padding = `10px ${gap}`;
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_MediaObject(node: MediaObject, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    // Same as ImageRow: its 30/70 columns need their own mj-section.
    node.annotations.defines_own_columns = true;
    if (this.theme.images.text_layout === 'stacked') {
      node.annotations.media_layout = 'stacked';
    } else {
      node.annotations.media_layout = 'columns';
      node.annotations.media_widths = splitMediaRatio(this.theme.images.media_ratio);
      // the image stays first in the DOM so it stacks on top on mobile
      node.annotations.media_direction = node.side === 'right' ? 'rtl' : null;
    }
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Image(node: Image, scope: ScopeStack): void {
    scope.push(node);
    this.markManualImageIfNeeded(node, scope);
    this.applyAuthorAttributes(node);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_ImageLink(node: ImageLink, scope: ScopeStack): void {
    scope.push(node);
    node.annotations.bold = Boolean(scope.get('is_in_strong'));
    this.genericVisit(node, scope); // reaches node.img -> visit_Image
    scope.pop(node);
  }

  visit_Heading(node: Heading, scope: ScopeStack): void {
    scope.push(node);
    Annotation.openAnchorRun(scope);
    scope.get<Document>('document')!.annotations.has_headings = true;
    // Only the first h1 of the document body is its title, and only if it
    // holds nothing but text.
    const slot = scope.get<(string | null)[]>('document_title') ?? [];
    const claimsTitle = node.level === 1 && !scope.get('in_text') && !slot.length;
    const parts: string[] = [];
    if (claimsTitle) {
      scope.recordTypes();
      scope.set('title_parts', parts);
    }
    this.markTextIfNeeded(node, scope);
    // Alignment rides the mj-text attribute; left is MJML's own default, so
    // nothing is emitted for it.
    const align = this.theme.headingAt(node.level).align;
    if (node.annotations.requires_text && align !== 'left') node.annotations.text_attrs = { align };
    this.genericVisit(node, scope);
    if (claimsTitle) {
      // listing what a title may hold rather than what it may not
      const plain = [...scope.types()].every((kind) => kind === 'BlockText' || kind === 'LiteralText');
      const text = strip(parts.join(''));
      slot.push(plain && text ? text : null);
    }
    scope.pop(node);
  }

  visit_LiteralText(node: LiteralText, scope: ScopeStack): void {
    scope.push(node);
    scope.get<string[]>('title_parts')?.push(node.value);
    this.markStyles(node, scope, node.value);
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Emphasis(node: Emphasis, scope: ScopeStack): void {
    scope.push(node);
    this.addStyle(scope, 'italic');
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Strong(node: Strong, scope: ScopeStack): void {
    scope.push(node);
    scope.set('is_in_strong', true);
    // The ask still says it was bold, for the URL factory, but its words
    // keep their own letters: on a feed a call to action is a line of text.
    // A bold link among words is emphasis, styled as such.
    if (!node.annotations.ask) this.addStyle(scope, 'bold');
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_StrikeThrough(node: StrikeThrough, scope: ScopeStack): void {
    scope.push(node);
    this.addStyle(scope, 'strikethrough');
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_UrlLink(node: UrlLink, scope: ScopeStack): void {
    const label = node.plainText();
    this.link(node, scope, !label || label === node.href || isAnAddress(label));
  }

  visit_MailLink(node: MailLink, scope: ScopeStack): void {
    const label = node.plainText();
    this.link(node, scope, !label || label === node.address || label === node.href);
  }

  visit_TelLink(node: TelLink, scope: ScopeStack): void {
    const label = node.plainText();
    this.link(node, scope, !label || label === node.number || label === node.href);
  }

  link(node: Link, scope: ScopeStack, labelIsAddress: boolean): void {
    scope.push(node);
    // a link inside bold text is the ask where no button exists
    node.annotations.bold = Boolean(scope.get('is_in_strong'));
    // A label that is an address already — the target itself, the one the
    // parser wrapped around a bare address, or another — is not a name for
    // it: where the target is shown, it is not shown twice, and its words
    // are no styled text.
    node.annotations.label_is_address = labelIsAddress;
    if (labelIsAddress) scope.set('is_in_address', true);
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Mention(node: Mention, scope: ScopeStack): void {
    scope.push(node);
    scope.set('is_in_mention', true);
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Hashtag(node: Hashtag, scope: ScopeStack): void {
    scope.push(node);
    // The mail may set it apart, when its theme says so; the feed never
    // touches it.
    const color = this.theme.hashtags.color;
    if (color) node.annotations.hashtag_style = `color: ${color};`;
    this.markTextIfNeeded(node, scope);
    scope.pop(node);
  }

  visit_CodeSpan(node: CodeSpan, scope: ScopeStack): void {
    scope.push(node);
    this.markStyles(node, scope, node.code);
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_InlineHtml(node: InlineHtml, scope: ScopeStack): void {
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    Annotation.markAnchor(node, scope);
    scope.pop(node);
  }

  /** A block where hand-written anchors pair up: an opening tag and its
   *  closing one sit in the same paragraph, heading, cell or item, whatever
   *  marks or images stand between them. */
  static openAnchorRun(scope: ScopeStack): void {
    scope.set('anchors', []);
  }

  /** Say which hand-written tags open and close an anchor, and hand the
   *  closing one the URL its opening tag carried: the text output shows it,
   *  the fragment rebuilds the anchor from it. Pairing an opening tag with
   *  its closing one is a matter of document order. */
  static markAnchor(node: InlineHtml, scope: ScopeStack): void {
    const pending = scope.get<[string | null, boolean][]>('anchors');
    if (!pending) return;
    const value = strip(node.value);
    const opening = ANCHOR_HREF.exec(value);
    if (opening) {
      // what runs something is no link, hand-written or not: its closing tag
      // is still its own, never an outer anchor's
      const href = runsSomething(opening[1] ?? '') ? null : (opening[1] ?? '');
      // an anchor inside another is no tag a page can hold: its address is
      // still said where words carry it
      const nested = pending.some(([outer]) => outer !== null);
      if (href !== null) {
        node.annotations.anchor_opens = href;
        node.annotations.anchor_nested = nested;
      }
      pending.push([href, nested]);
    } else if (value.toLowerCase() === '</a>' && pending.length) {
      const [href, nested] = pending.pop()!;
      if (href !== null) {
        node.annotations.anchor_href = href;
        node.annotations.anchor_nested = nested;
      }
    }
  }

  /** Say which bold link is the ask — where no button exists: alone on its
   *  line, blanks aside. Which line a node is on is a matter between
   *  siblings, so it belongs here rather than in a codegen. */
  static markTheAsks(node: BlockText): void {
    let line: Node[] = [];
    for (const child of [...node.children, new LineBreak()]) {
      if (!(child instanceof SoftBreak || child instanceof LineBreak)) {
        line.push(child);
        continue;
      }
      let alone = Annotation.alone(line);
      // through the marks that wrap it alone: `*__[Réserver](…)__*`
      while (alone instanceof Emphasis || alone instanceof StrikeThrough) alone = Annotation.alone(alone.children);
      if (alone instanceof Strong && alone.ask !== null) alone.annotations.ask = true;
      line = [];
    }
  }

  /** The one node of a run, blanks aside, or null. */
  static alone(nodes: Node[]): Node | null {
    const inner = nodes.filter((node) => !node.isBlank());
    return inner.length === 1 ? (inner[0] ?? null) : null;
  }

  markRawIfNeeded(node: Node, scope: ScopeStack): void {
    // Outside raw HTML, raw content must be wrapped in mj-raw to be valid
    // MJML.
    node.annotations.requires_raw = !Annotation.inRawHtml(scope);
  }

  visit_BlockHtml(node: BlockHtml, scope: ScopeStack): void {
    scope.push(node);
    this.markRawIfNeeded(node, scope);
    scope.pop(node);
  }

  visit_ThematicBreak(node: ThematicBreak, scope: ScopeStack): void {
    scope.push(node);
    node.annotations.divider_attrs = {
      'border-color': this.theme.divider.color,
      'border-width': this.theme.divider.width,
    };
    scope.pop(node);
  }

  visit_LineBreak(node: LineBreak, scope: ScopeStack): void {
    this.break(node, scope);
  }

  visit_SoftBreak(node: SoftBreak, scope: ScopeStack): void {
    this.break(node, scope);
  }

  break(node: LineBreak | SoftBreak, scope: ScopeStack): void {
    scope.push(node);
    if (!node.annotations.between_blocks) this.markTextIfNeeded(node, scope);
    scope.pop(node);
  }
}
