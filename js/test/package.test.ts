// What JavaScript adds of its own to the twin: values that must not change
// once built, and patterns that keep no state between two searches.

import { expect, test } from 'vitest';
import { BARE_DOMAIN, HASHTAG, Theme, THEMES } from '../src/index.js';
import { formatG } from '../src/stdlib.js';

test('a theme is a value, all the way down', () => {
  const dark = Theme.named('dark');
  expect(() => {
    (dark.text as { color: string }).color = 'red';
  }).toThrow(TypeError);
  expect(() => {
    (dark.headings.h1 as { size: string }).size = '99px';
  }).toThrow(TypeError);
  expect(THEMES.default?.headings.h1.size).toBe('28px');
});

test('an exported pattern answers the same twice', () => {
  expect([BARE_DOMAIN.test('exemple.com'), BARE_DOMAIN.test('exemple.com')]).toEqual([true, true]);
  expect([HASHTAG.test('#tag'), HASHTAG.test('#tag')]).toEqual([true, true]);
});

test('%g writes what Python writes', () => {
  expect([30, 33.3, 66.7, 100 - 33.3, 0.00001, 1234567].map(formatG)).toEqual([
    '30',
    '33.3',
    '66.7',
    '66.7',
    '1e-05',
    '1.23457e+06',
  ]);
});
