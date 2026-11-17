// SPDX-License-Identifier: Apache-2.0
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DAY_MS, dayIndex, dayToIso } from '../src/core/forecast.js';
import {
  calibration,
  forecast,
  gradeDue,
  parseProbability,
  parseTargetDate,
  record,
  scoreboard,
  searchAll,
} from '../src/core/service.js';

const NOW = '2026-11-17T12:00:00Z';
const TODAY = dayIndex(NOW);

// 2 items finished every day for the last 400 days, in Jira's own date format.
const FINISHED = [];
for (let d = 1; d <= 400; d++) {
  for (let k = 0; k < 2; k++) {
    const iso = new Date((TODAY - d) * DAY_MS + 9 * 3600 * 1000).toISOString().replace('Z', '+0000');
    FINISHED.push({ id: `h${d}-${k}`, key: `ENG-${1000 + d * 2 + k}`, fields: { statuscategorychangedate: iso } });
  }
}
const OPEN = Array.from({ length: 10 }, (_, i) => ({ id: `o${i}`, key: `ENG-${101 + i}` }));

// A fake /rest/api/3/search/jql that pages 100 at a time.
function fakeJira({ late = [] } = {}) {
  const calls = [];
  const search = async (body) => {
    calls.push(body);
    let pool;
    if (body.jql.startsWith('key in')) pool = OPEN.filter((i) => late.includes(i.key));
    else if (body.jql.includes('statusCategory = Done')) {
      const since = dayIndex(body.jql.match(/>= "(\d{4}-\d{2}-\d{2})"/)[1]);
      pool = FINISHED.filter((i) => dayIndex(i.fields.statuscategorychangedate) >= since);
    } else if (body.jql.includes('statusCategory != Done')) pool = OPEN;
    else throw new Error(`unexpected JQL ${body.jql}`);
    const start = body.nextPageToken ? Number(body.nextPageToken) : 0;
    const issues = pool.slice(start, start + body.maxResults);
    const next = start + body.maxResults;
    return next < pool.length ? { issues, nextPageToken: String(next), isLast: false } : { issues, isLast: true };
  };
  return { search, calls };
}

function memoryStore() {
  const m = new Map();
  return {
    m,
    get: async (k) => m.get(k),
    set: async (k, v) => void m.set(k, JSON.parse(JSON.stringify(v))),
    list: async (prefix) => [...m.entries()].filter(([k]) => k.startsWith(prefix)).map(([key, value]) => ({ key, value })),
  };
}

test('forecast reads history and open items through paged search', async () => {
  const { search, calls } = fakeJira();
  const r = await forecast({ search, now: NOW, scope: 'ENG', target: '2.4', targetDate: dayToIso(TODAY + 4) });
  assert.equal(r.ok, true);
  assert.equal(r.remaining, 10);
  assert.equal(r.finishedInWindow, 180);
  assert.equal(r.probability, 1);
  assert.equal(r.scopeJql, 'project = "ENG"');
  assert.equal(r.targetJql, '(project = "ENG") AND fixVersion = "2.4"');
  assert.ok(calls.some((c) => c.nextPageToken), 'history should need more than one page');
  const tight = await forecast({ search, now: NOW, scope: 'ENG', target: '2.4', targetDate: dayToIso(TODAY + 3) });
  assert.equal(tight.probability, 0);
});

test('forecast uses the project the user is in', async () => {
  const { search } = fakeJira();
  const r = await forecast({ search, now: NOW, projectKey: 'ENG', target: 'ENG-7', targetDate: dayToIso(TODAY + 30) });
  assert.equal(r.scopeJql, 'project = "ENG"');
  assert.equal(r.targetJql, 'parent = ENG-7');
});

test('calibration replays a year of history', async () => {
  const { search } = fakeJira();
  const c = await calibration({ search, now: NOW, scope: 'ENG' });
  assert.equal(c.ok, true);
  assert.equal(c.finishedItems, 730);
  assert.ok(c.origins >= 30);
  // Constant pace: every statement came true.
  for (const row of c.table) assert.equal(row.hitRate, 1);
});

test('record, grade the day after, and score', async () => {
  const { search } = fakeJira({ late: ['ENG-105'] });
  const store = memoryStore();
  const target = dayToIso(TODAY + 4);
  const r = await record({ search, store, now: NOW, scope: 'ENG', target: '2.4', targetDate: target, yourProbability: '70' });
  assert.equal(r.recorded, true);
  const saved = [...store.m.values()][0];
  assert.equal(saved.pHuman, 0.7);
  assert.equal(saved.pModel, 1);
  assert.equal(saved.keys.length, 10);
  assert.equal(saved.outcome, null);

  const early = await gradeDue({ search, store, now: `${target}T23:00:00Z` });
  assert.equal(early.graded, 0);
  const due = await gradeDue({ search, store, now: `${dayToIso(TODAY + 5)}T01:00:00Z` });
  assert.equal(due.graded, 1);
  const graded = [...store.m.values()][0];
  assert.equal(graded.outcome, 0);
  assert.equal(graded.lateCount, 1);

  const board = await scoreboard({ store });
  assert.equal(board.graded, 1);
  assert.equal(board.model.brier, 1);
  assert.equal(board.human.brier, 0.49);
  assert.equal(board.recent[0].outcome, 0);
});

test('searchAll stops when Jira repeats a page', async () => {
  const page = { issues: [{ id: '1', key: 'A-1' }], nextPageToken: 'same', isLast: false };
  let n = 0;
  const r = await searchAll(async () => (n++, page), 'x = y', ['key'], 1000);
  assert.equal(r.issues.length, 1);
  assert.ok(n <= 2, `called ${n} times`);
});

test('input checks', () => {
  assert.equal(parseTargetDate('2026-12-01', NOW), '2026-12-01');
  assert.throws(() => parseTargetDate('2026-02-30', NOW), /real calendar/);
  assert.throws(() => parseTargetDate('2026-11-01', NOW), /past/);
  assert.throws(() => parseTargetDate('next friday', NOW), /YYYY-MM-DD/);
  assert.equal(parseProbability('70'), 0.7);
  assert.equal(parseProbability(0.25), 0.25);
  assert.equal(parseProbability(''), null);
  assert.throws(() => parseProbability('-1'), /between/);
});
