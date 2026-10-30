// Runs every URL of the document through the client factory, in place —
// `inkletter/visitors/urls.py`. Runs last, after Annotation, so that what
// the document says about a link is already written in its node. Only
// addresses are offered: a URN, a `mailto:`, a `tel:` are left alone.

import type { Button, Image, ImageLink, UrlLink } from '../ast.js';
import type { URLFactory } from '../shortener.js';
import { NodeVisitor } from './generic.js';
import type { ScopeStack } from './scope.js';

// What locates something on the web, and may be shortened or uploaded: a
// web address, or a path relative to one — no scheme at all.
const REWRITABLE_SCHEMES = ['http', 'https', ''];

export class URLRewriter extends NodeVisitor {
  constructor(private readonly factory: URLFactory) {
    super();
  }

  visit_UrlLink(node: UrlLink, scope: ScopeStack): void {
    this.rewriteHref(node);
    this.genericVisit(node, scope);
  }

  visit_ImageLink(node: ImageLink, scope: ScopeStack): void {
    this.rewriteHref(node);
    this.genericVisit(node, scope); // reaches node.img -> visit_Image
  }

  visit_Button(node: Button, scope: ScopeStack): void {
    this.rewriteHref(node);
    this.genericVisit(node, scope);
  }

  static isRewritable(node: { scheme: string }): boolean {
    return REWRITABLE_SCHEMES.includes(node.scheme);
  }

  visit_Image(node: Image): void {
    if (URLRewriter.isRewritable(node)) {
      node.url = this.checked('rewriteImage', node.url, this.factory.rewriteImage(node.url));
    }
  }

  rewriteHref(node: UrlLink | ImageLink | Button): void {
    if (!URLRewriter.isRewritable(node)) return;
    const rewritten = this.factory.rewriteLink(
      node.href,
      node.annotations.button === true,
      node.annotations.bold === true,
    );
    node.href = this.checked('rewriteLink', node.href, rewritten);
  }

  checked(method: string, url: string, rewritten: string): string {
    if (typeof rewritten !== 'string') {
      throw new TypeError(`${this.factory.constructor.name}.${method} returned ${String(rewritten)} for ${url}; expected a string`);
    }
    return rewritten;
  }
}
