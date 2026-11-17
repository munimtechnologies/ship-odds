// SPDX-License-Identifier: Apache-2.0
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  finishedSinceClause,
  historyJql,
  lateJql,
  looksLikeJql,
  openJql,
  quote,
  scopeToJql,
  stripOrderBy,
  targetToJql,
} from '../src/core/jql.js';

test('quote escapes backslashes and quotes', () => {
  assert.equal(quote('a"b\\c'), '"a\\"b\\\\c"');
});

test('scope: project key, fallback, JQL with ORDER BY', () => {
  assert.equal(scopeToJql('ENG'), 'project = "ENG"');
  assert.equal(scopeToJql('', 'OPS'), 'project = "OPS"');
  assert.equal(scopeToJql(undefined, 'OPS'), 'project = "OPS"');
  assert.equal(scopeToJql('project = X AND type = Bug ORDER BY rank ASC'), 'project = X AND type = Bug');
  assert.throws(() => scopeToJql(''), /project/);
});

test('target: version name, epic key, JQL', () => {
  const s = 'project = "ENG"';
  assert.equal(targetToJql('2.4', s), '(project = "ENG") AND fixVersion = "2.4"');
  assert.equal(targetToJql('Q4 launch', s), '(project = "ENG") AND fixVersion = "Q4 launch"');
  assert.equal(targetToJql('ENG-12', s), 'parent = ENG-12');
  assert.equal(targetToJql('labels = q4 order by key', s), 'labels = q4');
  assert.throws(() => targetToJql('  ', s), /ship/);
});

test('looksLikeJql', () => {
  assert.equal(looksLikeJql('2.4'), false);
  assert.equal(looksLikeJql('fixVersion = 2.4'), true);
  assert.equal(looksLikeJql('key in (A-1)'), true);
  assert.equal(stripOrderBy('a = b ORDER BY c'), 'a = b');
});

test('finished-since prefers the resolution date, falls back to the status-category date', () => {
  assert.equal(
    finishedSinceClause('2026-08-19'),
    '(resolved >= "2026-08-19" OR (resolution is EMPTY AND statusCategoryChangedDate >= "2026-08-19"))',
  );
});

test('history, open and late clauses', () => {
  assert.equal(
    historyJql('project = "ENG"', '2026-08-19'),
    '(project = "ENG") AND statusCategory = Done AND ' +
      '(resolved >= "2026-08-19" OR (resolution is EMPTY AND statusCategoryChangedDate >= "2026-08-19"))',
  );
  assert.equal(openJql('parent = ENG-12'), '(parent = ENG-12) AND statusCategory != Done');
  assert.equal(
    lateJql(['ENG-1', 'bad key', 'OPS-22'], '2026-12-02'),
    'key in (ENG-1,OPS-22) AND (statusCategory != Done OR ' +
      '(resolved >= "2026-12-02" OR (resolution is EMPTY AND statusCategoryChangedDate >= "2026-12-02")))',
  );
  assert.throws(() => lateJql(['nope'], '2026-12-02'), /keys/);
});
