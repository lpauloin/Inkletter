// URL rewriting factories — `inkletter/shortener.py`. A client extends
// URLFactory and overrides only what concerns it: a shortener implements
// `rewriteLink` and leaves image sources untouched by inheritance.

export class URLFactory {
  /** The width of the links this factory produces, when it is fixed — a
   *  shortener's codes are all the same length. The LinkedIn output prices
   *  every link at it, so that a post is counted for what will be published
   *  before the short links exist. Null: each address counts for itself. */
  linkLength: number | null = null;

  /** Click URLs: links, image links, buttons. `isButton` when the link is the
   *  button, `isBold` when it sits inside bold text — how an output without
   *  buttons still tells the call to action from a link cited in passing. */
  rewriteLink(url: string, _isButton: boolean, _isBold: boolean): string {
    return url;
  }

  /** Image source URLs. */
  rewriteImage(url: string): string {
    return url;
  }
}
