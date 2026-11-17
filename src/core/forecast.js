// Ship Odds core: Monte Carlo throughput forecasts, their own track record,
// and odds corrected by that track record.
// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
//
// Pure functions only (no Forge imports), so they run under plain `node --test`.
// All day arithmetic is in whole UTC days.

export const DAY_MS = 86400000;

/** Fewest replayed past forecasts before Ship Odds will correct today's odds. */
export const MIN_PITS = 12;
/** Pseudo-observations that pull the correction toward "no correction". */
export const SHRINK_K = 10;

/** Small, fast, seedable PRNG (mulberry32). Returns floats in [0, 1). */
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function next() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Parse a Jira or ISO timestamp (Jira writes "+0000", JS wants "+00:00"). Returns ms or NaN. */
export function parseTime(value) {
  if (value instanceof Date) return value.getTime();
  if (typeof value === 'number') return value;
  if (typeof value !== 'string' || value.trim() === '') return NaN;
  let s = value.trim();
  s = s.replace(/([+-]\d{2})(\d{2})$/, '$1:$2');
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) s += 'T00:00:00Z';
  return Date.parse(s);
}

/** Whole UTC day number of a time. */
export function dayIndex(value) {
  const ms = parseTime(value);
  if (!Number.isFinite(ms)) throw new Error(`Not a date: ${value}`);
  return Math.floor(ms / DAY_MS);
}

/** "YYYY-MM-DD" for a UTC day number. */
export function dayToIso(day) {
  return new Date(day * DAY_MS).toISOString().slice(0, 10);
}

/**
 * Items finished per day for days in [startDay, endDay).
 * doneDays: array of UTC day numbers, one per finished item.
 */
export function dailyCounts(doneDays, startDay, endDay) {
  const n = Math.max(0, endDay - startDay);
  const counts = new Array(n).fill(0);
  for (const d of doneDays) {
    if (d >= startDay && d < endDay) counts[d - startDay] += 1;
  }
  return counts;
}

/** Nearest-rank quantile of an ascending array (q in (0, 1]). */
export function quantile(sorted, q) {
  if (!sorted.length) return NaN;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil(q * sorted.length) - 1));
  return sorted[idx];
}

/** How many values of an ascending array are <= x (binary search). */
export function countAtMost(sorted, x) {
  let lo = 0;
  let hi = sorted.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (sorted[mid] <= x) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

/**
 * Simulate how many days it takes to finish `remaining` items, drawing each
 * day's throughput from `samples` (bootstrap of past days). Returns an
 * ascending array of day counts (Infinity when maxDays is reached).
 */
export function simulateDaysToFinish(samples, remaining, runs, rng, maxDays = 3650) {
  const out = new Array(runs);
  const n = samples.length;
  for (let r = 0; r < runs; r++) {
    let done = 0;
    let d = 0;
    while (done < remaining && d < maxDays) {
      done += samples[Math.floor(rng() * n)];
      d += 1;
    }
    out[r] = done >= remaining ? d : Infinity;
  }
  return out.sort((a, b) => a - b);
}

/** Simulate total items finished over `horizonDays` days. Ascending array. */
export function simulateCount(samples, horizonDays, runs, rng) {
  const out = new Array(runs);
  const n = samples.length;
  for (let r = 0; r < runs; r++) {
    let total = 0;
    for (let d = 0; d < horizonDays; d++) total += samples[Math.floor(rng() * n)];
    out[r] = total;
  }
  return out.sort((a, b) => a - b);
}

/**
 * Randomized probability integral transform (PIT) of a whole-number outcome
 * under the model's simulated distribution: F(actual - 1) + u * P(actual).
 * If the model is calibrated, PITs are uniform on [0, 1]. PITs near 0 mean
 * the team did less than the model expected; near 1, more.
 */
export function pitOf(sortedTotals, actual, u) {
  const n = sortedTotals.length;
  const below = countAtMost(sortedTotals, actual - 1);
  const atMost = countAtMost(sortedTotals, actual);
  return (below + u * (atMost - below)) / n;
}

/**
 * Replay the model on the past and return one PIT per past forecast. Only
 * forecasts whose whole horizon ended by today are used, and each sees only
 * the windowDays before its own start, exactly like a live forecast would.
 */
export function pitHistory({
  doneDates,
  now,
  historyStart,
  windowDays = 90,
  horizonDays = 14,
  stepDays = 7,
  runs = 1000,
  seed = 11,
  maxOrigins = 60,
}) {
  const today = dayIndex(now);
  const doneDays = doneDates.map(dayIndex);
  const firstDay = historyStart != null ? dayIndex(historyStart) : Math.min(...doneDays);
  const lastOrigin = today - horizonDays;
  const firstOrigin = firstDay + windowDays;
  const pits = [];
  if (!doneDays.length || !Number.isFinite(firstDay) || lastOrigin < firstOrigin) {
    return { pits, horizonDays, windowDays };
  }
  const allCounts = dailyCounts(doneDays, firstDay, today);
  const rng = mulberry32(seed);
  const urng = mulberry32(seed + 1);
  for (let t = lastOrigin; t >= firstOrigin && pits.length < maxOrigins; t -= stepDays) {
    const samples = allCounts.slice(t - windowDays - firstDay, t - firstDay);
    if (samples.reduce((a, b) => a + b, 0) === 0) continue;
    const totals = simulateCount(samples, horizonDays, runs, rng);
    let actual = 0;
    for (let d = t; d < t + horizonDays; d++) actual += allCounts[d - firstDay];
    pits.push(pitOf(totals, actual, urng()));
  }
  return { pits, horizonDays, windowDays };
}

/**
 * Recalibration map G learned from past PITs (empirical CDF), shrunk toward
 * the identity with `k` pseudo-observations so a short history corrects only
 * a little. G(x) = (#{pit <= x} + k x) / (n + k).
 */
export function recalibrator(pits, k = SHRINK_K) {
  const s = [...pits].sort((a, b) => a - b);
  const n = s.length;
  return (x) => {
    const c = Math.min(1, Math.max(0, x));
    return (countAtMost(s, c) + k * c) / (n + k);
  };
}

/**
 * Corrected probability of "at least r items" given the raw model probability
 * p = P(total >= r) = 1 - F(r - 1): the calibrated CDF is G(F), so the answer
 * is 1 - G(1 - p). Monotone in p, keeps 0 at 0.
 */
export function correctProbability(p, G) {
  if (p == null || !Number.isFinite(p)) return p;
  return Math.min(1, Math.max(0, 1 - G(1 - p)));
}

/** Summary of past PITs: how often the team fell in the model's slow tail (bottom 15%). */
export function pitSummary(pits) {
  if (!pits.length) return null;
  const slow = pits.filter((p) => p <= 0.15).length / pits.length;
  const fast = pits.filter((p) => p >= 0.85).length / pits.length;
  const mean = pits.reduce((a, b) => a + b, 0) / pits.length;
  return { n: pits.length, mean: round(mean, 3), slowTail: round(slow, 3), fastTail: round(fast, 3) };
}

/**
 * Forecast when `remaining` items will be done, and the odds of finishing by targetDate.
 *
 * Day 1 of the simulation is "today" (the UTC day of `now`); history is the
 * `windowDays` whole days before today, so today's partial day is never sampled.
 *
 * If `pits` (from pitHistory) has at least MIN_PITS entries, the result also
 * has `corrected`: the same odds and dates after correcting for how the model's
 * past forecasts on this scope actually turned out.
 */
export function forecastCompletion({
  doneDates,
  now,
  remaining,
  targetDate,
  windowDays = 90,
  runs = 10000,
  seed = 1,
  pits = null,
  pitHorizonDays = null,
}) {
  const today = dayIndex(now);
  const doneDays = doneDates.map(dayIndex);
  const samples = dailyCounts(doneDays, today - windowDays, today);
  const finishedInWindow = samples.reduce((a, b) => a + b, 0);
  const base = {
    remaining,
    windowDays,
    finishedInWindow,
    throughputPerWeek: round((finishedInWindow / windowDays) * 7, 2),
    today: dayToIso(today),
    targetDate: targetDate ? dayToIso(dayIndex(targetDate)) : null,
    runs,
  };
  if (!Number.isInteger(remaining) || remaining < 0) {
    return { ok: false, reason: 'remaining must be a whole number of items, 0 or more', ...base };
  }
  if (remaining === 0) {
    return { ok: true, probability: targetDate ? 1 : null, dates: null, corrected: null, note: 'Nothing is left to do.', ...base };
  }
  if (finishedInWindow === 0) {
    return {
      ok: false,
      reason: `No items in scope were finished in the last ${windowDays} days, so there is no throughput to forecast from.`,
      ...base,
    };
  }
  const rng = mulberry32(seed);
  const days = simulateDaysToFinish(samples, remaining, runs, rng);
  const dateAt = (q) => {
    const d = quantile(days, q);
    return Number.isFinite(d) ? dayToIso(today + d - 1) : null;
  };
  // Raw P(done within `allowed` days, today included).
  const pDoneWithin = (allowed) => countAtMost(days, allowed) / runs;
  let probability = null;
  if (targetDate) probability = round(pDoneWithin(dayIndex(targetDate) - today + 1), 4);

  let corrected = null;
  if (Array.isArray(pits) && pits.length >= MIN_PITS) {
    const G = recalibrator(pits);
    const lastFinite = days.filter(Number.isFinite).pop();
    const correctedDateAt = (q) => {
      if (lastFinite == null) return null;
      for (let d = 1; d <= lastFinite; d++) {
        if (correctProbability(pDoneWithin(d), G) >= q) return dayToIso(today + d - 1);
      }
      return null; // beyond anything the simulation reached: say "later than we can tell"
    };
    corrected = {
      probability: probability == null ? null : round(correctProbability(probability, G), 4),
      dates: { p50: correctedDateAt(0.5), p85: correctedDateAt(0.85), p95: correctedDateAt(0.95) },
      basedOn: pitSummary(pits),
      horizonDays: pitHorizonDays,
      shrinkK: SHRINK_K,
    };
  }
  return {
    ok: true,
    probability,
    dates: { p50: dateAt(0.5), p85: dateAt(0.85), p95: dateAt(0.95) },
    corrected,
    ...base,
  };
}

/** Wilson score interval for k successes out of n (z = 1.96 by default). */
export function wilson(k, n, z = 1.96) {
  if (n === 0) return [0, 1];
  const p = k / n;
  const z2 = z * z;
  const denom = 1 + z2 / n;
  const centre = (p + z2 / (2 * n)) / denom;
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / denom;
  return [Math.max(0, centre - half), Math.min(1, centre + half)];
}

/**
 * Hindcast: replay the same model on the past and check how often its stated
 * odds came true. At each origin day t (every stepDays, newest first), the
 * model sees only the windowDays before t and forecasts items finished in
 * [t, t + horizonDays). For each confidence level L it states "at least X_L
 * items" where X_L is the (1 - L) lower quantile; its own probability for that
 * statement is P(total >= X_L) (>= L because counts are whole numbers). We
 * compare those stated probabilities with how often the statement held.
 *
 * Origins overlap when stepDays < horizonDays, so the outcomes are not
 * independent; the Wilson intervals are a rough guide, not a test.
 */
export function hindcast({
  doneDates,
  now,
  historyStart,
  windowDays = 90,
  horizonDays = 14,
  stepDays = 7,
  levels = [0.5, 0.7, 0.85, 0.95],
  runs = 2000,
  seed = 7,
  maxOrigins = 60,
}) {
  const today = dayIndex(now);
  const doneDays = doneDates.map(dayIndex);
  const firstDay = historyStart != null ? dayIndex(historyStart) : Math.min(...doneDays);
  const lastOrigin = today - horizonDays;
  const firstOrigin = firstDay + windowDays;
  const perLevel = levels.map((level) => ({ level, n: 0, hits: 0, statedSum: 0 }));
  let origins = 0;
  let skipped = 0;
  const examples = [];
  if (!doneDays.length || !Number.isFinite(firstDay) || lastOrigin < firstOrigin) {
    return {
      ok: false,
      reason: `Need at least ${windowDays + horizonDays} days of history (window ${windowDays} + horizon ${horizonDays}).`,
      windowDays,
      horizonDays,
      stepDays,
    };
  }
  const allCounts = dailyCounts(doneDays, firstDay, today);
  const sumRange = (a, b) => {
    let s = 0;
    for (let d = a; d < b; d++) s += allCounts[d - firstDay];
    return s;
  };
  const rng = mulberry32(seed);
  for (let t = lastOrigin; t >= firstOrigin && origins + skipped < maxOrigins; t -= stepDays) {
    const samples = allCounts.slice(t - windowDays - firstDay, t - firstDay);
    if (samples.reduce((a, b) => a + b, 0) === 0) {
      skipped += 1;
      continue;
    }
    origins += 1;
    const totals = simulateCount(samples, horizonDays, runs, rng);
    const actual = sumRange(t, t + horizonDays);
    const row = { origin: dayToIso(t), actual, atLeast: {} };
    perLevel.forEach((p) => {
      const x = quantile(totals, 1 - p.level);
      let ge = 0;
      for (const v of totals) if (v >= x) ge += 1;
      const stated = ge / runs;
      p.n += 1;
      p.statedSum += stated;
      if (actual >= x) p.hits += 1;
      row.atLeast[p.level] = x;
    });
    if (examples.length < 8) examples.push(row);
  }
  const table = perLevel.map((p) => {
    const hitRate = p.n ? p.hits / p.n : null;
    const stated = p.n ? p.statedSum / p.n : null;
    const [lo, hi] = wilson(p.hits, p.n);
    let verdict = 'not enough data';
    if (p.n >= 8) {
      if (stated > hi + 1e-9) verdict = 'overconfident';
      else if (stated < lo - 1e-9) verdict = 'underconfident';
      else verdict = 'consistent';
    }
    return {
      level: p.level,
      n: p.n,
      stated: round(stated, 3),
      hitRate: hitRate == null ? null : round(hitRate, 3),
      interval: [round(lo, 3), round(hi, 3)],
      verdict,
    };
  });
  return {
    ok: origins > 0,
    reason: origins > 0 ? undefined : 'Every past window had zero finished items.',
    windowDays,
    horizonDays,
    stepDays,
    origins,
    skipped,
    table,
    summary: summarizeCalibration(table, origins, horizonDays),
    examples,
  };
}

function summarizeCalibration(table, origins, horizonDays) {
  if (!origins) return 'No past forecasts could be replayed.';
  const judged = table.filter((r) => r.verdict !== 'not enough data');
  if (!judged.length) return `Only ${origins} past forecasts could be replayed; too few to judge calibration.`;
  const over = judged.filter((r) => r.verdict === 'overconfident').map((r) => pct(r.level));
  const under = judged.filter((r) => r.verdict === 'underconfident').map((r) => pct(r.level));
  const parts = judged.map((r) => `${pct(r.stated)} stated, ${pct(r.hitRate)} came true`);
  let head = `Replayed ${origins} past ${horizonDays}-day forecasts. `;
  if (!over.length && !under.length) head += 'Its odds matched what happened at every level checked. ';
  if (over.length) head += `Overconfident at ${over.join(', ')}: the corrected odds discount them. `;
  if (under.length) head += `Underconfident at ${under.join(', ')}: it was too cautious. `;
  return head + `(${parts.join('; ')}.)`;
}

/** Brier score and reliability for logged forecasts that have an outcome (0 or 1). */
export function scoreLedger(entries) {
  const graded = entries.filter((e) => e.outcome === 0 || e.outcome === 1);
  const brier = (key) => {
    const rows = graded.filter((e) => typeof e[key] === 'number');
    if (!rows.length) return { n: 0, brier: null };
    const s = rows.reduce((acc, e) => acc + (e[key] - e.outcome) ** 2, 0);
    return { n: rows.length, brier: round(s / rows.length, 4) };
  };
  const bins = [0, 0.2, 0.4, 0.6, 0.8].map((lo) => ({ from: lo, to: round(lo + 0.2, 1), n: 0, meanP: 0, hits: 0 }));
  for (const e of graded) {
    if (typeof e.pModel !== 'number') continue;
    const i = Math.min(bins.length - 1, Math.max(0, Math.floor(e.pModel * 5 + 1e-9)));
    bins[i].n += 1;
    bins[i].meanP += e.pModel;
    bins[i].hits += e.outcome;
  }
  return {
    total: entries.length,
    graded: graded.length,
    open: entries.length - graded.length,
    model: brier('pModel'),
    corrected: brier('pCorrected'),
    human: brier('pHuman'),
    reliability: bins
      .filter((b) => b.n)
      .map((b) => ({ from: b.from, to: b.to, n: b.n, meanP: round(b.meanP / b.n, 3), hitRate: round(b.hits / b.n, 3) })),
  };
}

export function round(x, digits) {
  if (x == null || !Number.isFinite(x)) return x;
  const f = 10 ** digits;
  return Math.round(x * f) / f;
}

function pct(x) {
  return `${Math.round(x * 100)}%`;
}
