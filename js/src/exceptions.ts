// Everything Inkletter raises on purpose — `inkletter/exceptions.py`. All
// three are failures of the input, and their messages are written for the
// author: what is wrong, and what to write instead.

/** Invalid theme definition (unknown key, bad type, unknown preset). */
export class ThemeError extends Error {
  override name = 'ThemeError';
}

/** The Markdown says something Inkletter cannot honour: an image attribute
 *  block with an unknown key, a length in a unit email cannot rely on, an
 *  alignment that is not one. */
export class MarkupError extends Error {
  override name = 'MarkupError';
}

/** The rendered text is longer than the destination accepts: raised rather
 *  than truncated, carrying what was measured and what was allowed. */
export class LengthError extends Error {
  override name = 'LengthError';

  constructor(
    public length: number,
    public limit: number,
    public what = 'post',
  ) {
    super(`the ${what} is ${length} characters long, ${limit} allowed (${length - limit} over)`);
  }
}
