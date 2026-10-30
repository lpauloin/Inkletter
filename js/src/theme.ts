// Themes: the look of the generated email — `inkletter/theme.py`.
//
// A theme is a value, sections grouped by concern, every field with a
// default. Built from a mapping (`Theme.fromDict`, the shape of a theme's
// TOML file, keys and all) or picked among the presets (`Theme.named`).
// Field names are the Python package's, so that one mapping makes the same
// theme on both sides.

import { Blue, Gray, Green, Red, Slate, WHITE, Yellow, type Hue } from './colors.js';
import { ThemeError } from './exceptions.js';
import { formatG } from './stdlib.js';

/** h1 through h6, in order. */
export const LEVELS = [1, 2, 3, 4, 5, 6] as const;

/** What an mj-* align attribute takes. */
export const ALIGNMENTS = ['left', 'center', 'right'] as const;

function validateAlignment(where: string, value: string): void {
  if (!(ALIGNMENTS as readonly string[]).includes(value)) {
    throw new ThemeError(`align '${value}' in [${where}] is not an alignment; use ${ALIGNMENTS.join(', ')}`);
  }
}

export interface Layout {
  width: string;
  background_color: string;
  content_background_color: string;
  section_padding: string;
}

export interface TextSection {
  font_family: string;
  font_size: string;
  line_height: string;
  color: string;
}

/** One heading level: how big it is, and where it sits. */
export interface HeadingLevel {
  size: string;
  align: string;
}

export interface Headings {
  font_family: string | null; // null inherits text.font_family
  color: string | null; // null inherits text.color
  font_weight: string;
  h1: HeadingLevel;
  h2: HeadingLevel;
  h3: HeadingLevel;
  h4: HeadingLevel;
  h5: HeadingLevel;
  h6: HeadingLevel;
}

export interface Links {
  color: string;
  underline: boolean;
}

export interface Hashtags {
  // null: a hashtag is text like the words around it
  color: string | null;
}

export interface Code {
  font_family: string;
  background_color: string;
  color: string;
}

export interface Quote {
  color: string;
  border_color: string;
  font_style: string;
}

export interface Divider {
  color: string;
  width: string;
}

export interface Buttons {
  background_color: string | null; // null inherits links.color
  color: string;
  border_radius: string;
  font_weight: string;
  padding: string; // mj-button inner-padding
  align: string;
}

export interface Images {
  align: string; // lone image narrower than the column
  row_gap: string; // horizontal padding inside image-row columns
  border_radius: string;
  text_layout: string; // media object: "columns" or "stacked"
  media_ratio: string; // image column width of a media object
}

export interface TableSection {
  border_color: string; // horizontal row rules
  cell_padding: string;
  header_color: string | null; // null inherits the text color
  header_background_color: string | null; // null means transparent
}

export interface ThemeSections {
  layout: Layout;
  text: TextSection;
  headings: Headings;
  links: Links;
  hashtags: Hashtags;
  code: Code;
  quote: Quote;
  divider: Divider;
  table: TableSection;
  images: Images;
  buttons: Buttons;
}

type SectionName = keyof ThemeSections;
type Section = ThemeSections[SectionName];
export type Fonts = readonly (readonly [string, string])[];

/** A theme as a mapping: sections of keys, a level's subsection, `fonts`. */
export type ThemeValue = string | boolean | null;
export type ThemeMapping = Record<string, Record<string, ThemeValue | Record<string, ThemeValue>>>;

const DEFAULTS: Readonly<ThemeSections> = {
  layout: { width: '600px', background_color: Gray.LIGHTEST, content_background_color: WHITE, section_padding: '16px 0' },
  text: { font_family: 'Helvetica, Arial, sans-serif', font_size: '14px', line_height: '1.6', color: Gray.DARK },
  headings: {
    font_family: null,
    color: null,
    font_weight: '700',
    h1: { size: '28px', align: 'left' },
    h2: { size: '22px', align: 'left' },
    h3: { size: '18px', align: 'left' },
    h4: { size: '16px', align: 'left' },
    h5: { size: '14px', align: 'left' },
    h6: { size: '13px', align: 'left' },
  },
  links: { color: Blue.DARK, underline: true },
  hashtags: { color: null },
  code: { font_family: 'Menlo, Consolas, monospace', background_color: Gray.LIGHTEST, color: Gray.DARKEST },
  quote: { color: Gray.BASE, border_color: Gray.LIGHT, font_style: 'italic' },
  divider: { color: Gray.LIGHT, width: '1px' },
  table: { border_color: Gray.LIGHT, cell_padding: '8px 12px', header_color: null, header_background_color: null },
  images: { align: 'center', row_gap: '8px', border_radius: '0', text_layout: 'columns', media_ratio: '30%' },
  buttons: {
    background_color: null,
    color: WHITE,
    border_radius: '6px',
    font_weight: '700',
    padding: '12px 24px',
    align: 'center',
  },
};

const SECTION_NAMES = Object.keys(DEFAULTS) as SectionName[];
const SECTIONS = [...SECTION_NAMES, 'fonts'];

export type ThemeOverrides = { [Name in SectionName]?: Partial<ThemeSections[Name]> } & {
  fonts?: Fonts | Record<string, string>;
};

export class Theme {
  readonly layout: Readonly<Layout>;
  readonly text: Readonly<TextSection>;
  readonly headings: Readonly<Headings>;
  readonly links: Readonly<Links>;
  readonly hashtags: Readonly<Hashtags>;
  readonly code: Readonly<Code>;
  readonly quote: Readonly<Quote>;
  readonly divider: Readonly<Divider>;
  readonly table: Readonly<TableSection>;
  readonly images: Readonly<Images>;
  readonly buttons: Readonly<Buttons>;
  // web fonts to load, name and stylesheet URL, in order
  readonly fonts: Fonts;

  constructor(overrides: ThemeOverrides = {}) {
    // a value, all the way down: no theme changes once built, nor its
    // sections, nor the defaults it was built from
    this.layout = Object.freeze({ ...DEFAULTS.layout, ...overrides.layout });
    this.text = Object.freeze({ ...DEFAULTS.text, ...overrides.text });
    const headings = { ...DEFAULTS.headings, ...overrides.headings };
    for (const number of LEVELS) headings[`h${number}`] = Object.freeze({ ...headings[`h${number}`] });
    this.headings = Object.freeze(headings);
    this.links = Object.freeze({ ...DEFAULTS.links, ...overrides.links });
    this.hashtags = Object.freeze({ ...DEFAULTS.hashtags, ...overrides.hashtags });
    this.code = Object.freeze({ ...DEFAULTS.code, ...overrides.code });
    this.quote = Object.freeze({ ...DEFAULTS.quote, ...overrides.quote });
    this.divider = Object.freeze({ ...DEFAULTS.divider, ...overrides.divider });
    this.table = Object.freeze({ ...DEFAULTS.table, ...overrides.table });
    this.images = Object.freeze({ ...DEFAULTS.images, ...overrides.images });
    this.buttons = Object.freeze({ ...DEFAULTS.buttons, ...overrides.buttons });
    for (const number of LEVELS) validateAlignment(`headings.h${number}`, this.headingAt(number).align);
    validateAlignment('buttons', this.buttons.align);
    validateAlignment('images', this.images.align);
    this.fonts = validateFonts(overrides.fonts ?? [], this.text);
    Object.freeze(this);
  }

  static fromDict(data: ThemeMapping): Theme {
    if (typeof data !== 'object' || data === null || Array.isArray(data)) {
      throw new ThemeError('a theme must be a mapping of sections');
    }
    const overrides: Record<string, unknown> = {};
    for (const [name, values] of Object.entries(data)) {
      if (!SECTIONS.includes(name)) {
        throw new ThemeError(`unknown section '[${name}]'; valid sections: ${[...SECTIONS].sort().join(', ')}`);
      }
      // the fonts are a free table of names, not a fixed set of keys
      overrides[name] = name === 'fonts' ? values : buildSection(name, values, DEFAULTS[name as SectionName]);
    }
    return new Theme(overrides as ThemeOverrides);
  }

  static named(name: string): Theme {
    const theme = THEMES[name];
    if (!theme) throw new ThemeError(`unknown theme '${name}'; available themes: ${Object.keys(THEMES).sort().join(', ')}`);
    return theme;
  }

  headingAt(number: number): HeadingLevel {
    return this.headings[`h${number}` as `h${(typeof LEVELS)[number]}`];
  }

  /** The button background, inheriting the links color when unset. */
  buttonBackground(): string {
    return this.buttons.background_color || this.links.color;
  }

  /** CSS rules for the raw HTML living inside mj-text blocks, emitted in an
   *  `<mj-style inline="inline">` so MJML inlines them into the tags. */
  toCss(): string {
    const headingFont = this.headings.font_family || this.text.font_family;
    const headingColor = this.headings.color || this.text.color;
    const decoration = this.links.underline ? 'underline' : 'none';
    return [
      `${LEVELS.map((number) => `h${number}`).join(', ')} { font-family: ${headingFont};` +
        ` color: ${headingColor};` +
        ` font-weight: ${this.headings.font_weight};` +
        ' line-height: 1.3; margin: 0; }',
      ...LEVELS.map((number) => `h${number} { font-size: ${this.headingAt(number).size}; }`),
      `a { color: ${this.links.color}; text-decoration: ${decoration}; }`,
      'p { margin: 0 0 12px; }',
      'p:last-child { margin-bottom: 0; }',
      `blockquote { color: ${this.quote.color};` +
        ` font-style: ${this.quote.font_style};` +
        ` border-left: 3px solid ${this.quote.border_color};` +
        ' margin: 0; padding: 2px 0 2px 14px; }',
      `code { font-family: ${this.code.font_family};` +
        ` background-color: ${this.code.background_color};` +
        ` color: ${this.code.color};` +
        ' padding: 2px 4px; border-radius: 3px; }',
      `pre { font-family: ${this.code.font_family};` +
        ` background-color: ${this.code.background_color};` +
        ` color: ${this.code.color};` +
        ' margin: 0; padding: 12px; border-radius: 6px;' +
        ' overflow-x: auto; }',
      'ul, ol { margin: 0; padding-left: 24px; }',
    ].join('\n');
  }
}

/** A value must have the shape of the field it fills. */
function checkValue(fallback: unknown, section: string, key: string, value: unknown): void {
  if (typeof fallback === 'boolean') {
    if (typeof value !== 'boolean') throw new ThemeError(`key '${key}' in [${section}] must be a bool`);
  } else if (typeof value !== 'string' && !(fallback === null && value === null)) {
    throw new ThemeError(`key '${key}' in [${section}] must be a str`);
  }
}

/** One section of a theme, built from its mapping and merged onto `base` —
 *  which is what lets a subsection name one key and inherit the rest. */
function buildSection(name: string, values: unknown, base: Section | HeadingLevel): Section | HeadingLevel {
  if (typeof values !== 'object' || values === null || Array.isArray(values)) {
    throw new ThemeError(`section '[${name}]' must be a mapping`);
  }
  const known = base as unknown as Record<string, unknown>;
  const built: Record<string, unknown> = { ...known };
  for (const [key, value] of Object.entries(values)) {
    if (!(key in known)) {
      throw new ThemeError(`unknown key '${key}' in [${name}]; valid keys: ${Object.keys(known).sort().join(', ')}`);
    }
    if (typeof value === 'object' && value !== null) {
      // a subsection, such as [headings.h1]: merged onto that level's own
      // default, so that naming the alignment does not mean repeating the size
      built[key] = buildSection(`${name}.${key}`, value, known[key] as HeadingLevel);
      continue;
    }
    checkValue(known[key], name, key, value);
    built[key] = value;
  }
  return built as unknown as Section;
}

/** The names of a CSS stack, as written, in order. */
function fontTokens(fontFamily: string): string[] {
  return fontFamily.split(',').map((name) => name.trim());
}

function unquoted(name: string): string {
  return name.replace(/^["']+|["']+$/g, '');
}

/** How the stack spells `name`, quotes and all: MJML only hooks an mj-font
 *  to a component whose font-family names it literally. */
function asWritten(name: string, fontFamily: string): string {
  const key = unquoted(name.trim()).toLowerCase();
  return fontTokens(fontFamily).find((token) => unquoted(token).toLowerCase() === key) ?? name;
}

/** `[fonts]` as pairs, refusing what cannot load: MJML only loads a font
 *  the template uses in a component attribute, and text.font_family is the
 *  only theme setting that reaches one. */
function validateFonts(fonts: Fonts | Record<string, string>, text: TextSection): Fonts {
  const pairs = Array.isArray(fonts) ? fonts : Object.entries(fonts);
  const used = new Set(fontTokens(text.font_family).map((name) => unquoted(name).toLowerCase()));
  const seen = new Set<string>();
  return pairs.map((pair) => {
    if (!Array.isArray(pair) || pair.length !== 2) throw new ThemeError('[fonts] must map a font name to a URL');
    const [name, href] = pair as [unknown, unknown];
    if (typeof name !== 'string' || !name.trim()) throw new ThemeError('a font name in [fonts] cannot be empty');
    if (typeof href !== 'string') throw new ThemeError(`font '${name}' in [fonts] must be a URL string`);
    if (!href.startsWith('http://') && !href.startsWith('https://')) {
      throw new ThemeError(
        `font '${name}' in [fonts] must be an http:// or https:// URL; an email loads its fonts over the network`,
      );
    }
    const key = name.trim().toLowerCase();
    if (seen.has(key)) throw new ThemeError(`font '${name}' is declared twice in [fonts]`);
    seen.add(key);
    if (!used.has(key)) {
      throw new ThemeError(
        `font '${name}' is declared in [fonts] but missing from text.font_family; MJML only loads a font ` +
          'used in a component attribute, so add it there to load it, or drop the declaration and rely on the fallback',
      );
    }
    return [asWritten(name, text.font_family), href] as const;
  });
}

/** A media-object image ratio like "30%" split into (image, text) widths. */
export function splitMediaRatio(ratio: string): [string, string] {
  const value = /^\s*[+-]?(\d+\.?\d*|\.\d+)\s*%?\s*$/.test(ratio) ? Number.parseFloat(ratio.trim().replace(/%$/, '')) : -1;
  if (!(value > 0 && value < 100)) {
    throw new ThemeError(
      `invalid media_ratio '${ratio}' in [images]; expected a percentage between 0 and 100, e.g. '30%'`,
    );
  }
  return [`${formatG(value)}%`, `${formatG(100 - value)}%`];
}

// The theme applied whenever none is provided
export const DEFAULT_THEME = new Theme();

// --- Presets ---

// Standard, email-safe font stacks used by the presets
const SANS = 'Helvetica, Arial, sans-serif';
const HUMANIST = "'Trebuchet MS', Helvetica, Arial, sans-serif";
const WIDE_SANS = 'Verdana, Geneva, sans-serif';
const COMPACT_SANS = 'Tahoma, Verdana, sans-serif';
const SERIF = "Georgia, 'Times New Roman', serif";
const ELEGANT_SERIF = "'Palatino Linotype', 'Book Antiqua', Palatino, Georgia, serif";

function hueTheme(hue: Hue, textFont = SANS, headingFont: string | null = null): Theme {
  return new Theme({
    layout: { background_color: hue.LIGHTEST },
    text: { font_family: textFont },
    headings: { color: hue.DARKEST, font_family: headingFont },
    links: { color: hue.DARK },
    quote: { color: Gray.BASE, border_color: hue.LIGHT },
    divider: { color: hue.LIGHT },
    code: { background_color: hue.LIGHTEST, color: hue.DARKEST },
    table: { border_color: hue.LIGHT, header_color: hue.DARKEST, header_background_color: hue.LIGHTEST },
  });
}

export const THEMES: Readonly<Record<string, Theme>> = {
  default: new Theme(),
  dark: new Theme({
    layout: { background_color: Slate.DARKEST, content_background_color: Slate.DARK },
    text: { color: Slate.LIGHT },
    headings: { color: WHITE, font_family: HUMANIST },
    links: { color: Blue.LIGHT },
    code: { background_color: Slate.DARKEST, color: Slate.LIGHT },
    quote: { color: Slate.BASE, border_color: Slate.BASE },
    divider: { color: Slate.BASE },
    table: { border_color: Slate.LIGHT, header_color: WHITE, header_background_color: Slate.DARKEST },
    // light CTA popping on the dark slate
    buttons: { background_color: Blue.LIGHT, color: Slate.DARKEST },
  }),
  crystal: new Theme({
    layout: { background_color: Slate.LIGHTEST },
    text: { color: Slate.DARK },
    headings: { color: Slate.DARKEST, font_family: ELEGANT_SERIF },
    links: { color: Blue.BASE },
    quote: { color: Slate.BASE, border_color: Blue.LIGHT },
    divider: { color: Slate.LIGHT },
    code: { background_color: Slate.LIGHTEST, color: Slate.DARKEST },
    table: { border_color: Slate.LIGHT, header_background_color: Slate.LIGHTEST },
  }),
  blue: hueTheme(Blue, COMPACT_SANS, HUMANIST),
  green: hueTheme(Green, SERIF, SERIF),
  red: hueTheme(Red, SANS, SERIF),
  yellow: hueTheme(Yellow, WIDE_SANS, HUMANIST),
};
