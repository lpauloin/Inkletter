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
  type Link,
  List,
  ListItem,
  LiteralText,
  MediaObject,
  Mention,
  type Node,
  Paragraph,
  SoftBreak,
  StrikeThrough,
  Strong,
  Table,
  TableCell,
  TableHeaderCell,
  TaskListItem,
  ThematicBreak,
} from '../ast.js';
import { strip } from '../stdlib.js';
import { splitMediaRatio, type Theme } from '../theme.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';

/** The href of a hand-written opening anchor, read for the text output
 *  only — the HTML half passes the tag through untouched. */
export const ANCHOR_HREF = /^<a\s[^>]*\bhref\s*=\s*["']([^"']*)["']/i;

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
    const theme = this.theme;
    const imageAttrs: Record<string, string> = { align: theme.images.align };
    if (!this.linkAttributes) {
      // a document converted without link attributes renders exactly as it
      // did before they existed
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
    scope.pop(node);
  }

  /** Bold, italic, strikethrough: the styles in force below, carried down to
   *  every text they cover. */
  addStyle(scope: ScopeStack, style: string): void {
    scope.set('styles', new Set([...(scope.get<ReadonlySet<string>>('styles') ?? []), style]));
  }

  markStyles(node: Node, scope: ScopeStack): void {
    // a mention's name is never dressed: it is what the platform matches
    const styles = scope.get<ReadonlySet<string>>('styles');
    if (styles?.size && !scope.get('is_in_mention')) node.annotations.styles = styles;
  }

  markTextIfNeeded(node: Node, scope: ScopeStack): void {
    if (
      !scope.get('in_text') &&
      !scope.get('is_in_table_cell') &&
      !scope.get('is_in_list_item') &&
      !scope.get('is_in_button')
    ) {
      node.annotations.requires_text = true;
      scope.set('in_text', true);
    }
  }

  markManualTableIfNeeded(node: Node, scope: ScopeStack): void {
    if (scope.get('is_in_list')) node.annotations.requires_manual_table = true;
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
    // Inside the raw HTML of an mj-text, of an mj-table or of an mj-button
    // label, an mj-image would leak as an unknown tag: render a plain <img>
    // instead, with its style ready to emit.
    if (scope.get('in_text') || scope.get('is_in_table') || scope.get('is_in_button')) {
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
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_TaskListItem(node: TaskListItem, scope: ScopeStack): void {
    scope.push(node);
    scope.set('is_in_list_item', true);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_ListItem(node: ListItem, scope: ScopeStack): void {
    scope.push(node);
    scope.set('is_in_list_item', true);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Paragraph(node: Paragraph, scope: ScopeStack): void {
    scope.push(node);
    // At flow level each paragraph gets its own mj-text, and the padding
    // between them separates them. Inside a raw-HTML context — a quote, a
    // list item, a cell — the paragraph must carry its own tag.
    node.annotations.requires_paragraph_tag = Boolean(
      scope.get('in_text') || scope.get('is_in_table_cell') || scope.get('is_in_list_item'),
    );
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_BlockText(node: BlockText, scope: ScopeStack): void {
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    Annotation.markInlineAnchors(node);
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
    scope.set('is_in_table', true);
    this.markManualTableIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_TableHeaderCell(node: TableHeaderCell, scope: ScopeStack): void {
    scope.push(node);
    scope.set('is_in_table_cell', true);
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
    scope.set('is_in_table_cell', true);
    const table = this.theme.table;
    node.annotations.cell_style = `border-bottom: 1px solid ${table.border_color}; padding: ${table.cell_padding};`;
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_Button(node: Button, scope: ScopeStack): void {
    scope.push(node);
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
    this.markManualImageIfNeeded(node, scope);
    this.genericVisit(node, scope); // reaches node.img -> visit_Image
    scope.pop(node);
  }

  visit_Heading(node: Heading, scope: ScopeStack): void {
    scope.push(node);
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
    this.markStyles(node, scope);
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
    // The ask — a link alone in bold, where no button exists — still says it
    // was bold, for the URL factory, but its words keep their own letters.
    if (node.ask === null) this.addStyle(scope, 'bold');
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

  visit_UrlLink(node: Link, scope: ScopeStack): void {
    this.link(node, scope);
  }

  visit_MailLink(node: Link, scope: ScopeStack): void {
    this.link(node, scope);
  }

  visit_TelLink(node: Link, scope: ScopeStack): void {
    this.link(node, scope);
  }

  link(node: Link, scope: ScopeStack): void {
    scope.push(node);
    // a link inside bold text is the ask where no button exists
    node.annotations.bold = Boolean(scope.get('is_in_strong'));
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
    this.markStyles(node, scope);
    this.markTextIfNeeded(node, scope);
    this.genericVisit(node, scope);
    scope.pop(node);
  }

  visit_InlineHtml(node: InlineHtml, scope: ScopeStack): void {
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    scope.pop(node);
  }

  /** Say which hand-written tags open and close an anchor, and hand the
   *  closing one the URL its opening tag carried: the text output shows it,
   *  the fragment rebuilds the anchor from it. Pairing an opening tag with
   *  its closing one is a matter between siblings. */
  static markInlineAnchors(node: BlockText): void {
    const pending: string[] = [];
    for (const child of node.children) {
      if (!(child instanceof InlineHtml)) continue;
      const value = strip(child.value);
      const opening = ANCHOR_HREF.exec(value);
      if (opening) {
        child.annotations.anchor_opens = opening[1] ?? '';
        pending.push(opening[1] ?? '');
      }
      else if (value.toLowerCase() === '</a>' && pending.length) child.annotations.anchor_href = pending.pop() ?? '';
    }
  }

  markRawIfNeeded(node: Node, scope: ScopeStack): void {
    // Outside of any raw-HTML context, raw content must be wrapped in mj-raw
    // to be valid MJML.
    node.annotations.requires_raw = !(
      scope.get('in_text') ||
      scope.get('is_in_table_cell') ||
      scope.get('is_in_list_item') ||
      scope.get('is_in_button')
    );
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
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    scope.pop(node);
  }

  visit_SoftBreak(node: SoftBreak, scope: ScopeStack): void {
    scope.push(node);
    this.markTextIfNeeded(node, scope);
    scope.pop(node);
  }
}
