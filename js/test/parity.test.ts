// The scenarios `scripts/parity.py` wrote with the Python package: every
// document its suite renders, and those of `parity/documents.json`. The
// JavaScript package must fall on the same characters — the post and its
// count, the fragment, the MJML — or on the same refusal.

import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import {
  parseMarkdownToHtmlFragment,
  parseMarkdownToMjml,
  renderLinkedin,
  Theme,
  type ThemeMapping,
  URLFactory,
} from '../src/index.js';

interface Case {
  name: string;
  source: string;
  unicode_styling?: boolean;
  link_length?: number;
  factory?: 'marking';
  bold_link_is_button?: boolean;
  link_attributes?: boolean;
  theme?: ThemeMapping;
  expected?: string;
  length?: number;
  lines?: [string, number, [string, string, number][]][];
  unrendered_formatting?: boolean;
  unrendered_headings?: boolean;
  error?: string;
  message?: string;
}

class Width extends URLFactory {
  constructor(linkLength: number) {
    super();
    this.linkLength = linkLength;
  }
}

class Marking extends URLFactory {
  override rewriteLink(url: string, isButton: boolean, isBold: boolean): string {
    return `${url}#${isButton ? 'button' : isBold ? 'bold' : 'link'}`;
  }

  override rewriteImage(url: string): string {
    return `img:${url}`;
  }
}

function factoryOf(scenario: Case): URLFactory | null {
  if (scenario.factory === 'marking') return new Marking();
  if (scenario.link_length !== undefined) return new Width(scenario.link_length);
  return null;
}

function casesOf(output: string): Case[] {
  const url = new URL(`../../parity/${output}.json`, import.meta.url);
  return (JSON.parse(readFileSync(url, 'utf8')) as { cases: Case[] }).cases;
}

/** What a render says, in the shape the scenario wrote it. */
function answered(render: () => Partial<Case>): Partial<Case> {
  try {
    return render();
  } catch (refusal) {
    if (refusal instanceof Error && ['LengthError', 'MarkupError', 'ThemeError'].includes(refusal.name)) {
      return { error: refusal.name, message: refusal.message };
    }
    throw refusal;
  }
}

function expectedOf(scenario: Case): Partial<Case> {
  const { error, message, expected, length, lines, unrendered_formatting, unrendered_headings } = scenario;
  if (error !== undefined) return { error, message };
  if (length === undefined) return { expected };
  return { expected, length, lines, unrendered_formatting, unrendered_headings };
}

const options = (scenario: Case) => ({
  boldLinkIsButton: scenario.bold_link_is_button ?? true,
  linkAttributes: scenario.link_attributes ?? true,
  urlFactory: factoryOf(scenario),
});

describe('the post: the same text, the same count, the same lines', () => {
  test.each(casesOf('linkedin').map((scenario) => [scenario.name, scenario] as const))('%s', (_, scenario) => {
    const found = answered(() => {
      const render = renderLinkedin(scenario.source, {
        unicodeStyling: scenario.unicode_styling ?? false,
        urlFactory: factoryOf(scenario),
      });
      return {
        expected: render.text,
        length: render.length,
        lines: render.lines.map((line): [string, number, [string, string, number][]] => [
          line.text,
          line.cost,
          line.segments.map((segment): [string, string, number] => [segment.kind, segment.display, segment.cost]),
        ]),
        unrendered_formatting: render.unrenderedFormatting,
        unrendered_headings: render.unrenderedHeadings,
      };
    });
    expect(found).toEqual(expectedOf(scenario));
  });
});

describe('the HTML fragment: the same characters', () => {
  test.each(casesOf('html_fragment').map((scenario) => [scenario.name, scenario] as const))('%s', (_, scenario) => {
    const found = answered(() => ({ expected: parseMarkdownToHtmlFragment(scenario.source, options(scenario)) }));
    expect(found).toEqual(expectedOf(scenario));
  });
});

describe('the MJML: the same characters', () => {
  test.each(casesOf('mjml').map((scenario) => [scenario.name, scenario] as const))('%s', (_, scenario) => {
    const found = answered(() => ({
      expected: parseMarkdownToMjml(scenario.source, {
        ...options(scenario),
        theme: scenario.theme ? Theme.fromDict(scenario.theme) : null,
      }),
    }));
    expect(found).toEqual(expectedOf(scenario));
  });
});

test('a divergence introduced on purpose fails — the comparison is not vacuous', () => {
  const [scenario] = casesOf('html_fragment');
  if (!scenario?.expected) throw new Error('no fragment scenario');
  expect(parseMarkdownToHtmlFragment(scenario.source, options(scenario))).not.toEqual(`${scenario.expected} `);
});
