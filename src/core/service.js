// Ship Odds: the app's operations, with Jira search and storage passed in.
// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
//
// `search(body)` must POST body to /rest/api/3/search/jql and return the JSON.
// `store` needs get(key), set(key, value), list(prefix) -> [{key, value}].

import { DAY_MS, dayIndex, dayToIso, forecastCompletion, hindcast, parseTime, pitHistory, scoreLedger } from './forecast.js';
import { historyJql, lateJql, openJql, scopeToJql, targetToJql } from './jql.js';

export const LIMITS = {
  historyIssues: 5000, // finished items read for throughput
  openIssues: 1000, // open items in a target
  pageSize: 100,
  maxPages: 60,
  windowDays: { min: 14, max: 365, default: 90 },
  historyDays: 365,
  pitHorizon: { min: 7, max: 56 },
};

/** Page through enhanced JQL search, guarding against repeating pages. */
export async function searchAll(search, jql, fields, limit) {
  const issues = [];
  const seen = new Set();
  let token;
  for (let page = 0; page < LIMITS.maxPages; page++) {
    const body = { jql, maxResults: LIMITS.pageSize, fields };
    if (token) body.nextPageToken = token;
    const res = await search(body);
    const batch = (res && res.issues) || [];
    let fresh = 0;
    for (const issue of batch) {
      const id = issue.id || issue.key;
      if (seen.has(id)) continue;
      seen.add(id);
      issues.push(issue);
      fresh += 1;
      if (issues.length >= limit) return { issues, truncated: true };
    }
    if (res.isLast || !res.nextPageToken || res.nextPageToken === token || fresh === 0) break;
    token = res.nextPageToken;
  }
  return { issues, truncated: false };
}

/**
 * When an issue was finished: its resolution date, else its status-category
 * change date (for workflows that never set a resolution). Same rule as
 * finishedSinceClause in jql.js, so the JQL count and these dates agree.
 */
export function doneTime(issue) {
  const f = (issue && issue.fields) || {};
  for (const v of [f.resolutiondate, f.statuscategorychangedate]) {
    const t = parseTime(v || '');
    if (Number.isFinite(t)) return t;
  }
  return null;
}

export function clampWindow(windowDays) {
  const w = Number.parseInt(windowDays, 10);
  if (!Number.isFinite(w)) return LIMITS.windowDays.default;
  return Math.min(LIMITS.windowDays.max, Math.max(LIMITS.windowDays.min, w));
}

export function parseTargetDate(text, now) {
  const s = (text == null ? '' : String(text)).trim();
  if (!s) throw new Error('Give a target date as YYYY-MM-DD.');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) throw new Error(`Target date "${s}" is not in YYYY-MM-DD form.`);
  const ms = parseTime(s);
  const day = Number.isFinite(ms) ? Math.floor(ms / DAY_MS) : NaN;
  if (!Number.isFinite(day) || dayToIso(day) !== s) throw new Error(`Target date "${s}" is not a real calendar date.`);
  if (day < dayIndex(now)) throw new Error(`Target date ${s} is in the past.`);
  return s;
}

export function parseProbability(value) {
  if (value == null || value === '') return null;
  let p = Number(value);
  if (!Number.isFinite(p)) throw new Error('Your probability must be a number such as 0.7 or 70.');
  if (p > 1 && p <= 100) p /= 100;
  if (p < 0 || p > 1) throw new Error('Your probability must be between 0 and 1 (or 0 and 100%).');
  return p;
}

async function throughputHistory(search, scopeJql, now, days) {
  const since = dayToIso(dayIndex(now) - days);
  const jql = historyJql(scopeJql, since);
  const { issues, truncated } = await searchAll(
    search,
    jql,
    ['resolutiondate', 'statuscategorychangedate'],
    LIMITS.historyIssues,
  );
  const doneDates = issues.map(doneTime).filter((t) => t != null);
  return { jql, since, doneDates, truncated };
}

/** Horizon at which past forecasts are replayed to learn the correction. */
export function pitHorizonFor(targetIsoDate, now) {
  const days = dayIndex(targetIsoDate) - dayIndex(now) + 1;
  return Math.min(LIMITS.pitHorizon.max, Math.max(LIMITS.pitHorizon.min, days));
}

/**
 * Odds that the target's open items are all done by targetDate: the raw Monte
 * Carlo odds, and (with enough history) the odds corrected by how this
 * scope's past forecasts actually turned out.
 */
export async function forecast({ search, now, scope, target, targetDate, windowDays, projectKey }) {
  const scopeJql = scopeToJql(scope, projectKey);
  const targetJql = targetToJql(target, scopeJql);
  const date = parseTargetDate(targetDate, now);
  const w = clampWindow(windowDays);
  const warnings = [];

  // One read of the past year serves both the forecast window and the replay.
  // If the year is too big to read whole, fall back to the window alone.
  let history = await throughputHistory(search, scopeJql, now, LIMITS.historyDays);
  let pits = null;
  const pitHorizon = pitHorizonFor(date, now);
  if (history.truncated) {
    warnings.push(`More than ${LIMITS.historyIssues} items finished in the past year, so the odds are not corrected by past accuracy.`);
    history = await throughputHistory(search, scopeJql, now, w);
    if (history.truncated) warnings.push(`Read only the first ${LIMITS.historyIssues} finished items; throughput may be understated.`);
  } else {
    pits = pitHistory({
      doneDates: history.doneDates,
      now,
      historyStart: history.since,
      windowDays: w,
      horizonDays: pitHorizon,
    }).pits;
  }

  const open = await searchAll(search, openJql(targetJql), ['key'], LIMITS.openIssues);
  const keys = open.issues.map((i) => i.key).filter(Boolean);
  const result = forecastCompletion({
    doneDates: history.doneDates,
    now,
    remaining: keys.length,
    targetDate: date,
    windowDays: w,
    pits,
    pitHorizonDays: pitHorizon,
  });
  if (open.truncated) warnings.push(`Target has more than ${LIMITS.openIssues} open items; only that many were counted.`);
  if (result.ok && result.remaining > 0 && !result.corrected && pits) {
    warnings.push(`Only ${pits.length} past forecasts could be replayed (12 needed), so the odds are not corrected yet.`);
  }
  return {
    ...result,
    scopeJql,
    targetJql,
    openKeys: keys,
    warnings,
    assumptions:
      'Assumes the next weeks look like the last ' +
      `${w} days of finished work in this scope, that items are similar in size, and that no new items are added to the target.` +
      (result.corrected
        ? ` The corrected odds also assume this scope's forecasts will miss in the same way they did over the past year (learned from ${result.corrected.basedOn.n} replayed ${pitHorizon}-day forecasts).`
        : ''),
  };
}

/** Replay the model on this scope's past and report how often its odds came true. */
export async function calibration({ search, now, scope, windowDays, horizonDays, projectKey }) {
  const scopeJql = scopeToJql(scope, projectKey);
  const w = clampWindow(windowDays);
  const h = Math.min(56, Math.max(7, Number.parseInt(horizonDays, 10) || 14));
  const history = await throughputHistory(search, scopeJql, now, LIMITS.historyDays);
  const result = hindcast({
    doneDates: history.doneDates,
    now,
    historyStart: history.since,
    windowDays: w,
    horizonDays: h,
  });
  return {
    ...result,
    scopeJql,
    historySince: history.since,
    finishedItems: history.doneDates.length,
    warnings: history.truncated ? [`Read only the first ${LIMITS.historyIssues} finished items.`] : [],
  };
}

const LEDGER = 'forecast:';

/** Forecast and write it down, with an optional human probability, to be graded later. */
export async function record({ search, store, now, scope, target, targetDate, windowDays, projectKey, yourProbability, accountId }) {
  const pHuman = parseProbability(yourProbability);
  const f = await forecast({ search, now, scope, target, targetDate, windowDays, projectKey });
  if (!f.ok) return { recorded: false, ...f };
  const createdAt = new Date(parseTime(now)).toISOString();
  const id = `${createdAt.replace(/[^0-9]/g, '').slice(0, 14)}-${Math.floor(Math.random() * 1e6)}`;
  const entry = {
    id,
    createdAt,
    createdBy: accountId || null,
    scopeJql: f.scopeJql,
    targetJql: f.targetJql,
    targetDate: f.targetDate,
    remaining: f.remaining,
    keys: f.openKeys,
    pModel: f.probability,
    pCorrected: f.corrected ? f.corrected.probability : null,
    pHuman,
    outcome: f.remaining === 0 ? 1 : null,
    gradedAt: f.remaining === 0 ? createdAt : null,
  };
  await store.set(LEDGER + id, entry);
  return { recorded: true, id, ...f };
}

/** Grade every logged forecast whose target day has fully passed (UTC). */
export async function gradeDue({ search, store, now }) {
  const today = dayIndex(now);
  const entries = await store.list(LEDGER);
  let graded = 0;
  for (const { key, value } of entries) {
    if (!value || value.outcome === 0 || value.outcome === 1) continue;
    const targetDay = dayIndex(value.targetDate);
    if (targetDay >= today) continue;
    const keys = value.keys || [];
    let late = 0;
    for (let i = 0; i < keys.length; i += 100) {
      const chunk = keys.slice(i, i + 100);
      const res = await searchAll(search, lateJql(chunk, dayToIso(targetDay + 1)), ['key'], chunk.length);
      late += res.issues.length;
    }
    // Deleted or moved issues no longer match the key search; they count as done.
    value.outcome = late === 0 ? 1 : 0;
    value.lateCount = late;
    value.gradedAt = new Date(parseTime(now)).toISOString();
    await store.set(key, value);
    graded += 1;
  }
  return { graded };
}

/** Score of all logged forecasts: raw model, corrected model and people, Brier score (lower is better). */
export async function scoreboard({ store }) {
  const entries = (await store.list(LEDGER)).map((e) => e.value).filter(Boolean);
  entries.sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
  const score = scoreLedger(entries);
  return {
    ...score,
    recent: entries.slice(0, 20).map((e) => ({
      id: e.id,
      createdAt: e.createdAt,
      targetJql: e.targetJql,
      targetDate: e.targetDate,
      remaining: e.remaining,
      pModel: e.pModel,
      pCorrected: e.pCorrected == null ? null : e.pCorrected,
      pHuman: e.pHuman,
      outcome: e.outcome,
    })),
    note: 'Brier score: 0 is perfect, 0.25 is what always saying 50% earns. Each forecast is graded the day after its target date.',
  };
}

export { DAY_MS };
