// Ship Odds: Forge entry points (UI resolver, Rovo/MCP actions, daily grading).
// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.

import api, { route } from '@forge/api';
import Resolver from '@forge/resolver';
import { kvs, WhereConditions } from '@forge/kvs';
import { calibration, forecast, gradeDue, record, scoreboard } from './core/service.js';

// Reads run as the person asking, so nobody sees odds for issues they can't browse.
function searcher(asApp = false) {
  return async (body) => {
    const client = asApp ? api.asApp() : api.asUser();
    const res = await client.requestJira(route`/rest/api/3/search/jql`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Jira search failed (${res.status}): ${text.slice(0, 300)}`);
    }
    return res.json();
  };
}

const store = {
  get: (key) => kvs.get(key),
  set: (key, value) => kvs.set(key, value),
  async list(prefix) {
    const out = [];
    let cursor;
    for (let i = 0; i < 100; i++) {
      let q = kvs.query().where('key', WhereConditions.beginsWith(prefix)).limit(20);
      if (cursor) q = q.cursor(cursor);
      const page = await q.getMany();
      out.push(...page.results);
      if (!page.nextCursor) break;
      cursor = page.nextCursor;
    }
    return out;
  },
};

async function safely(fn) {
  try {
    return await fn();
  } catch (err) {
    return { ok: false, error: String((err && err.message) || err) };
  }
}

// ---- UI Kit project page ----
const resolver = new Resolver();
resolver.define('forecast', ({ payload, context }) =>
  safely(() => forecast({ search: searcher(), now: new Date(), projectKey: projectOf(context), ...pick(payload) })),
);
resolver.define('calibration', ({ payload, context }) =>
  safely(() => calibration({ search: searcher(), now: new Date(), projectKey: projectOf(context), ...pick(payload) })),
);
resolver.define('record', ({ payload, context }) =>
  safely(() =>
    record({
      search: searcher(),
      store,
      now: new Date(),
      projectKey: projectOf(context),
      accountId: context && context.accountId,
      ...pick(payload),
    }),
  ),
);
resolver.define('scoreboard', () => safely(() => scoreboard({ store })));
export const handler = resolver.getDefinitions();

// ---- Rovo agent actions and MCP tools (payload = inputs + context) ----
export async function forecastAction(payload) {
  return safely(() =>
    forecast({ search: searcher(), now: new Date(), projectKey: payloadProject(payload), ...pick(payload) }),
  ).then(forAgent);
}

export async function calibrationAction(payload) {
  return safely(() =>
    calibration({ search: searcher(), now: new Date(), projectKey: payloadProject(payload), ...pick(payload) }),
  );
}

export async function recordAction(payload, context) {
  return safely(() =>
    record({
      search: searcher(),
      store,
      now: new Date(),
      projectKey: payloadProject(payload),
      accountId: context && context.principal && context.principal.accountId,
      ...pick(payload),
    }),
  ).then(forAgent);
}

export async function scoreboardAction() {
  return safely(() => scoreboard({ store }));
}

// ---- Daily grading (runs as the app) ----
export async function gradeDaily() {
  return safely(() => gradeDue({ search: searcher(true), store, now: new Date() }));
}

// ---- helpers ----
const FIELDS = ['scope', 'target', 'targetDate', 'windowDays', 'horizonDays', 'yourProbability'];

function pick(payload) {
  const out = {};
  for (const k of FIELDS) if (payload && payload[k] != null && payload[k] !== '') out[k] = payload[k];
  return out;
}

function projectOf(context) {
  return (context && context.extension && context.extension.project && context.extension.project.key) || undefined;
}

function payloadProject(payload) {
  return (payload && payload.context && payload.context.jira && payload.context.jira.projectKey) || undefined;
}

// Agents don't need every open key; keep the answer short.
function forAgent(result) {
  if (!result || !Array.isArray(result.openKeys)) return result;
  const { openKeys, ...rest } = result;
  return { ...rest, openKeysSample: openKeys.slice(0, 10) };
}
