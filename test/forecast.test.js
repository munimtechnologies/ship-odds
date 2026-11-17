// SPDX-License-Identifier: Apache-2.0
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DAY_MS,
  dailyCounts,
  dayIndex,
  dayToIso,
  forecastCompletion,
  hindcast,
  mulberry32,
  parseTime,
  quantile,
  scoreLedger,
  wilson,
} from '../src/core/forecast.js';

const NOW = '2026-11-17T12:00:00Z';
const TODAY = dayIndex(NOW);

// One timestamp per finished item: counts[i] items on day (TODAY - counts.length + i), at noon UTC.
function datesFromCounts(counts) {
  const out = [];
  const start = TODAY - counts.length;
  counts.forEach((c, i) => {
    for (let k = 0; k < c; k++) out.push(new Date((start + i) * DAY_MS + 12 * 3600 * 1000).toISOString());
  });
  return out;
}

test('parseTime reads Jira +0000 offsets and plain dates', () => {
  assert.equal(parseTime('2026-11-10T14:03:22.123+0000'), Date.parse('2026-11-10T14:03:22.123Z'));
  assert.equal(parseTime('2026-11-10T14:03:22.123-0500'), Date.parse('2026-11-10T19:03:22.123Z'));
  assert.equal(parseTime('2026-11-10'), Date.parse('2026-11-10T00:00:00Z'));
  assert.ok(Number.isNaN(parseTime('')));
  assert.equal(dayToIso(dayIndex('2026-11-17')), '2026-11-17');
});

test('dailyCounts and nearest-rank quantile', () => {
  assert.deepEqual(dailyCounts([10, 10, 12, 9, 15], 10, 13), [2, 0, 1]);
  const s = [1, 2, 3, 4];
  assert.equal(quantile(s, 0.5), 2);
  assert.equal(quantile(s, 0.85), 4);
  assert.equal(quantile(s, 1), 4);
  assert.equal(quantile(s, 0.01), 1);
});

test('constant throughput gives exact dates and 0/1 odds', () => {
  const doneDates = datesFromCounts(new Array(90).fill(2));
  const ok = forecastCompletion({ doneDates, now: NOW, remaining: 10, targetDate: dayToIso(TODAY + 4), runs: 500 });
  assert.equal(ok.ok, true);
  assert.equal(ok.probability, 1);
  assert.equal(ok.dates.p50, dayToIso(TODAY + 4));
  assert.equal(ok.dates.p95, dayToIso(TODAY + 4));
  assert.equal(ok.throughputPerWeek, 14);
  const late = forecastCompletion({ doneDates, now: NOW, remaining: 10, targetDate: dayToIso(TODAY + 3), runs: 500 });
  assert.equal(late.probability, 0);
});

test('today is not sampled, and old items outside the window are ignored', () => {
  const doneDates = [NOW, NOW, NOW, new Date((TODAY - 200) * DAY_MS).toISOString()];
  const r = forecastCompletion({ doneDates, now: NOW, remaining: 3, targetDate: dayToIso(TODAY + 10) });
  assert.equal(r.ok, false);
  assert.match(r.reason, /No items/);
});

test('nothing left means certain; bad remaining is rejected', () => {
  const r = forecastCompletion({ doneDates: [], now: NOW, remaining: 0, targetDate: dayToIso(TODAY + 1) });
  assert.equal(r.ok, true);
  assert.equal(r.probability, 1);
  assert.equal(forecastCompletion({ doneDates: [], now: NOW, remaining: -1 }).ok, false);
});

test('same seed, same answer; odds rise with more time', () => {
  const rng = mulberry32(3);
  const counts = Array.from({ length: 90 }, () => Math.floor(rng() * 4));
  const doneDates = datesFromCounts(counts);
  const a = forecastCompletion({ doneDates, now: NOW, remaining: 40, targetDate: dayToIso(TODAY + 20), seed: 9 });
  const b = forecastCompletion({ doneDates, now: NOW, remaining: 40, targetDate: dayToIso(TODAY + 20), seed: 9 });
  assert.deepEqual(a, b);
  const later = forecastCompletion({ doneDates, now: NOW, remaining: 40, targetDate: dayToIso(TODAY + 40), seed: 9 });
  assert.ok(later.probability >= a.probability);
  assert.ok(a.dates.p50 <= a.dates.p85 && a.dates.p85 <= a.dates.p95);
});

test('hindcast on a steady team is roughly calibrated', () => {
  const rng = mulberry32(42);
  const counts = Array.from({ length: 400 }, () => Math.floor(rng() * 5));
  const doneDates = datesFromCounts(counts);
  const h = hindcast({ doneDates, now: NOW, historyStart: dayToIso(TODAY - 400) });
  assert.equal(h.ok, true);
  assert.ok(h.origins >= 30, `origins ${h.origins}`);
  const row = (lvl) => h.table.find((r) => r.level === lvl);
  assert.ok(row(0.95).stated >= 0.95);
  assert.ok(row(0.95).hitRate >= 0.7, JSON.stringify(row(0.95)));
  assert.ok(row(0.5).hitRate >= 0.2 && row(0.5).hitRate <= 0.95, JSON.stringify(row(0.5)));
  assert.equal(typeof h.summary, 'string');
});

test('hindcast flags a team whose pace keeps falling as overconfident', () => {
  const counts = Array.from({ length: 400 }, (_, i) => Math.max(0, 10 - Math.floor(i / 40)));
  const doneDates = datesFromCounts(counts);
  const h = hindcast({ doneDates, now: NOW, historyStart: dayToIso(TODAY - 400) });
  assert.equal(h.ok, true);
  const r85 = h.table.find((r) => r.level === 0.85);
  assert.ok(r85.n >= 8);
  assert.ok(r85.hitRate < 0.3, JSON.stringify(r85));
  assert.equal(r85.verdict, 'overconfident');
  assert.match(h.summary, /Overconfident/);
});

test('hindcast needs enough history', () => {
  const doneDates = datesFromCounts(new Array(50).fill(1));
  const h = hindcast({ doneDates, now: NOW, historyStart: dayToIso(TODAY - 50) });
  assert.equal(h.ok, false);
  assert.match(h.reason, /history/);
});

test('wilson interval', () => {
  assert.deepEqual(wilson(0, 0), [0, 1]);
  const [lo, hi] = wilson(5, 10);
  assert.ok(lo < 0.5 && hi > 0.5 && lo > 0.2 && hi < 0.8);
});

test('ledger Brier scores for model and people', () => {
  const s = scoreLedger([
    { pModel: 0.8, outcome: 1 },
    { pModel: 0.6, pHuman: 0.9, outcome: 0 },
    { pModel: 0.5, outcome: null },
  ]);
  assert.equal(s.total, 3);
  assert.equal(s.graded, 2);
  assert.equal(s.open, 1);
  assert.equal(s.model.n, 2);
  assert.equal(s.model.brier, 0.2);
  assert.equal(s.human.n, 1);
  assert.equal(s.human.brier, 0.81);
  assert.equal(s.reliability.length, 2);
});
