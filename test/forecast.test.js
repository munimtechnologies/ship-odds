// SPDX-License-Identifier: Apache-2.0
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DAY_MS,
  MIN_PITS,
  correctProbability,
  countAtMost,
  dailyCounts,
  dayIndex,
  dayToIso,
  forecastCompletion,
  hindcast,
  mulberry32,
  parseTime,
  pitHistory,
  pitOf,
  quantile,
  recalibrator,
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

// A team whose pace keeps sliding: about 6 a day a year ago, about 1 a day now, with noise.
function slidingTeam(days = 365, seed = 5) {
  const rng = mulberry32(seed);
  return Array.from({ length: days }, (_, i) => {
    const mean = 6 - (5 * i) / days;
    return Math.max(0, Math.round(mean + (rng() - 0.5) * 3));
  });
}

test('parseTime reads Jira +0000 offsets and plain dates', () => {
  assert.equal(parseTime('2026-11-10T14:03:22.123+0000'), Date.parse('2026-11-10T14:03:22.123Z'));
  assert.equal(parseTime('2026-11-10T14:03:22.123-0500'), Date.parse('2026-11-10T19:03:22.123Z'));
  assert.equal(parseTime('2026-11-10'), Date.parse('2026-11-10T00:00:00Z'));
  assert.ok(Number.isNaN(parseTime('')));
  assert.equal(dayToIso(dayIndex('2026-11-17')), '2026-11-17');
});

test('dailyCounts, nearest-rank quantile and countAtMost', () => {
  assert.deepEqual(dailyCounts([10, 10, 12, 9, 15], 10, 13), [2, 0, 1]);
  const s = [1, 2, 3, 4];
  assert.equal(quantile(s, 0.5), 2);
  assert.equal(quantile(s, 0.85), 4);
  assert.equal(quantile(s, 1), 4);
  assert.equal(quantile(s, 0.01), 1);
  assert.equal(countAtMost([1, 2, 2, 3], 2), 3);
  assert.equal(countAtMost([1, 2, 2, 3], 0), 0);
  assert.equal(countAtMost([1, 2, 2, 3], 9), 4);
  assert.equal(countAtMost([1, 2, Infinity], 5), 2);
});

test('constant throughput gives exact dates and 0/1 odds', () => {
  const doneDates = datesFromCounts(new Array(90).fill(2));
  const ok = forecastCompletion({ doneDates, now: NOW, remaining: 10, targetDate: dayToIso(TODAY + 4), runs: 500 });
  assert.equal(ok.ok, true);
  assert.equal(ok.probability, 1);
  assert.equal(ok.dates.p50, dayToIso(TODAY + 4));
  assert.equal(ok.dates.p95, dayToIso(TODAY + 4));
  assert.equal(ok.throughputPerWeek, 14);
  assert.equal(ok.corrected, null, 'no past forecasts given, so nothing to correct');
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

test('pitOf is the randomized PIT of a whole-number outcome', () => {
  const totals = [1, 2, 2, 3];
  assert.equal(pitOf(totals, 2, 0), 0.25);
  assert.equal(pitOf(totals, 2, 1), 0.75);
  assert.equal(pitOf(totals, 0, 0.5), 0);
  assert.equal(pitOf(totals, 9, 0.5), 1);
});

test('recalibrator: no history means no change; it is monotone and shrunk', () => {
  const id = recalibrator([]);
  for (const p of [0, 0.1, 0.5, 0.85, 1]) assert.ok(Math.abs(correctProbability(p, id) - p) < 1e-12);
  // Every past outcome fell in the slow 10% of the model's range.
  const slow = recalibrator(new Array(30).fill(0.05));
  const c85 = correctProbability(0.85, slow);
  assert.ok(c85 < 0.85, `corrected ${c85}`);
  // Shrinkage: 30 observations plus 10 pseudo-observations, so not all the way down.
  assert.ok(c85 > 0.1, `corrected ${c85}`);
  let prev = -1;
  for (let p = 0; p <= 1.0001; p += 0.05) {
    const c = correctProbability(Math.min(1, p), slow);
    assert.ok(c >= prev - 1e-12);
    prev = c;
  }
  assert.equal(correctProbability(0, slow), 0);
});

test('PITs of a steady team are roughly uniform; a sliding team sits in the slow tail', () => {
  const rng = mulberry32(42);
  const steady = datesFromCounts(Array.from({ length: 365 }, () => Math.floor(rng() * 5)));
  const a = pitHistory({ doneDates: steady, now: NOW, historyStart: dayToIso(TODAY - 365), horizonDays: 14 });
  assert.ok(a.pits.length >= 30, `pits ${a.pits.length}`);
  const meanA = a.pits.reduce((x, y) => x + y, 0) / a.pits.length;
  assert.ok(meanA > 0.3 && meanA < 0.7, `steady mean PIT ${meanA}`);
  for (const p of a.pits) assert.ok(p >= 0 && p <= 1);

  const sliding = datesFromCounts(slidingTeam());
  const b = pitHistory({ doneDates: sliding, now: NOW, historyStart: dayToIso(TODAY - 365), horizonDays: 14 });
  const meanB = b.pits.reduce((x, y) => x + y, 0) / b.pits.length;
  assert.ok(meanB < 0.3, `sliding mean PIT ${meanB}`);
});

test('corrected odds and dates for a sliding team are more cautious than the raw ones', () => {
  const doneDates = datesFromCounts(slidingTeam());
  const { pits } = pitHistory({ doneDates, now: NOW, historyStart: dayToIso(TODAY - 365), horizonDays: 21 });
  assert.ok(pits.length >= MIN_PITS);
  const r = forecastCompletion({
    doneDates,
    now: NOW,
    remaining: 32, // about 1.6 a day lately, 21 days: a toss-up for the raw model
    targetDate: dayToIso(TODAY + 20),
    pits,
    pitHorizonDays: 21,
    runs: 4000,
  });
  assert.equal(r.ok, true);
  assert.ok(r.corrected, 'corrected odds expected');
  assert.ok(r.probability > 0.05 && r.probability < 0.999, `raw ${r.probability}`);
  assert.ok(r.corrected.probability < r.probability, JSON.stringify({ raw: r.probability, c: r.corrected.probability }));
  assert.equal(r.corrected.basedOn.n, pits.length);
  assert.equal(r.corrected.horizonDays, 21);
  const later = (a, b) => b == null || (a != null && a >= b);
  assert.ok(later(r.corrected.dates.p85 == null ? '9999' : r.corrected.dates.p85, r.dates.p85));
  assert.ok(r.corrected.dates.p50 == null || r.corrected.dates.p50 >= r.dates.p50);
});

test('too few past forecasts: no correction', () => {
  const doneDates = datesFromCounts(new Array(120).fill(2));
  const r = forecastCompletion({
    doneDates,
    now: NOW,
    remaining: 10,
    targetDate: dayToIso(TODAY + 10),
    pits: new Array(MIN_PITS - 1).fill(0.5),
  });
  assert.equal(r.corrected, null);
});

test('wilson interval', () => {
  assert.deepEqual(wilson(0, 0), [0, 1]);
  const [lo, hi] = wilson(5, 10);
  assert.ok(lo < 0.5 && hi > 0.5 && lo > 0.2 && hi < 0.8);
});

test('ledger Brier scores for model, corrected model and people', () => {
  const s = scoreLedger([
    { pModel: 0.8, pCorrected: 0.7, outcome: 1 },
    { pModel: 0.6, pCorrected: 0.4, pHuman: 0.9, outcome: 0 },
    { pModel: 0.5, outcome: null },
  ]);
  assert.equal(s.total, 3);
  assert.equal(s.graded, 2);
  assert.equal(s.open, 1);
  assert.equal(s.model.n, 2);
  assert.equal(s.model.brier, 0.2);
  assert.equal(s.corrected.n, 2);
  assert.equal(s.corrected.brier, 0.125);
  assert.equal(s.human.n, 1);
  assert.equal(s.human.brier, 0.81);
  assert.equal(s.reliability.length, 2);
});
