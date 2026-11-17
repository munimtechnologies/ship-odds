// Ship Odds: JQL builders.
// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.

/** Quote a value for JQL: "..." with backslashes and quotes escaped. */
export function quote(value) {
  return `"${String(value).replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

/** Drop a trailing ORDER BY so the clause can be wrapped in parentheses. */
export function stripOrderBy(jql) {
  return String(jql).replace(/\border\s+by\b[\s\S]*$/i, '').trim();
}

/** True when the text reads like JQL rather than a bare name. */
export function looksLikeJql(text) {
  return /[=~<>!()]|\s(in|not in|is|is not|was|and|or)\s/i.test(` ${text} `);
}

const PROJECT_KEY = /^[A-Z][A-Z0-9_]{0,254}$/;

/**
 * Scope = where throughput is measured: a project key ("ENG") or any JQL.
 * Falls back to the project the user is looking at.
 */
export function scopeToJql(scope, fallbackProjectKey) {
  const s = (scope == null ? '' : String(scope)).trim();
  if (!s) {
    if (fallbackProjectKey) return `project = ${quote(fallbackProjectKey)}`;
    throw new Error('Say which project (key such as ENG) or JQL to measure throughput on.');
  }
  if (PROJECT_KEY.test(s)) return `project = ${quote(s)}`;
  const body = stripOrderBy(s);
  if (!body) throw new Error('The scope JQL is empty.');
  return body;
}

/**
 * Target = the work that has to ship: JQL, or a version name inside the scope
 * (an epic key such as ENG-12 also works: its child issues).
 */
export function targetToJql(target, scopeJql) {
  const t = (target == null ? '' : String(target)).trim();
  if (!t) throw new Error('Say what has to ship: a version name, an epic key, or JQL.');
  if (looksLikeJql(t)) {
    const body = stripOrderBy(t);
    if (!body) throw new Error('The target JQL is empty.');
    return body;
  }
  if (/^[A-Z][A-Z0-9_]*-\d+$/.test(t)) return `parent = ${t}`;
  return `(${scopeJql}) AND fixVersion = ${quote(t)}`;
}

/**
 * "Finished on or after a day": the resolution date when the item has one
 * (it survives CSV imports and migrations), else the status-category change
 * date (for workflows that never set a resolution). doneTime() in service.js
 * applies the same rule to the dates it reads, so counts and dates agree.
 */
export function finishedSinceClause(isoDate) {
  const d = quote(isoDate);
  return `(resolved >= ${d} OR (resolution is EMPTY AND statusCategoryChangedDate >= ${d}))`;
}

/** Items finished in scope since a day ("YYYY-MM-DD"). */
export function historyJql(scopeJql, sinceIsoDate) {
  return `(${scopeJql}) AND statusCategory = Done AND ${finishedSinceClause(sinceIsoDate)}`;
}

/** Items of the target that are not done yet. */
export function openJql(targetJql) {
  return `(${targetJql}) AND statusCategory != Done`;
}

/**
 * Which of `keys` were NOT finished by the end of targetIsoDate.
 * dayAfterIsoDate is the UTC day after the target.
 */
export function lateJql(keys, dayAfterIsoDate) {
  const safe = keys.filter((k) => /^[A-Z][A-Z0-9_]*-\d+$/.test(k));
  if (!safe.length) throw new Error('No valid issue keys to grade.');
  return `key in (${safe.join(',')}) AND (statusCategory != Done OR ${finishedSinceClause(dayAfterIsoDate)})`;
}
