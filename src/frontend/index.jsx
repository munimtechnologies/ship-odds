// Ship Odds: Jira project page (UI Kit).
// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.

import React, { useEffect, useState } from 'react';
import ForgeReconciler, {
  Box,
  Button,
  DynamicTable,
  Heading,
  Inline,
  Lozenge,
  SectionMessage,
  Spinner,
  Stack,
  Strong,
  Text,
  Textfield,
  useProductContext,
} from '@forge/react';
import { invoke } from '@forge/bridge';

const pct = (p) => (p == null ? '-' : `${Math.round(p * 100)}%`);

function table(head, rows) {
  return {
    head: { cells: head.map((content, i) => ({ key: `h${i}`, content })) },
    rows: rows.map((cells, r) => ({
      key: `r${r}`,
      cells: cells.map((content, i) => ({ key: `c${r}-${i}`, content })),
    })),
  };
}

function Calibration({ cal }) {
  if (!cal) return <Spinner />;
  if (cal.error || !cal.ok) {
    return <SectionMessage appearance="information"><Text>{cal.error || cal.reason}</Text></SectionMessage>;
  }
  const t = table(
    ['Odds the model gave', 'How often it came true', 'Forecasts', 'Verdict'],
    cal.table.map((r) => [
      pct(r.stated),
      `${pct(r.hitRate)} (${pct(r.interval[0])} to ${pct(r.interval[1])})`,
      String(r.n),
      <Lozenge appearance={r.verdict === 'consistent' ? 'success' : r.verdict === 'not enough data' ? 'default' : 'moved'}>
        {r.verdict}
      </Lozenge>,
    ]),
  );
  return (
    <Stack space="space.100">
      <Text>{cal.summary}</Text>
      <DynamicTable head={t.head} rows={t.rows} />
      <Text>
        Replayed on {cal.finishedItems} items finished since {cal.historySince}, using {cal.windowDays}-day
        windows. Past windows overlap, so treat the ranges as a rough guide.
      </Text>
    </Stack>
  );
}

function Result({ res }) {
  if (!res) return null;
  if (res.error || !res.ok) {
    return <SectionMessage appearance="warning"><Text>{res.error || res.reason}</Text></SectionMessage>;
  }
  return (
    <SectionMessage appearance="success" title={`${pct(res.probability)} chance to finish by ${res.targetDate}`}>
      <Text>
        {res.remaining} open items. Half of 10,000 simulated futures finish by {res.dates ? res.dates.p50 : '-'}; 85% by{' '}
        {res.dates ? res.dates.p85 : '-'}; 95% by {res.dates ? res.dates.p95 : '-'}.
      </Text>
      <Text>
        Based on {res.finishedInWindow} items finished in the last {res.windowDays} days ({res.throughputPerWeek} a week).{' '}
        {res.assumptions}
      </Text>
      {res.recorded ? <Text>Recorded. It will be graded the day after {res.targetDate}.</Text> : null}
      {(res.warnings || []).map((w) => (
        <Text>{w}</Text>
      ))}
    </SectionMessage>
  );
}

function Scoreboard({ board }) {
  if (!board) return <Spinner />;
  if (board.error) return <Text>{board.error}</Text>;
  const t = table(
    ['Made', 'Target', 'By', 'Model', 'Person', 'Outcome'],
    board.recent.map((e) => [
      e.createdAt.slice(0, 10),
      e.targetJql,
      e.targetDate,
      pct(e.pModel),
      pct(e.pHuman),
      e.outcome == null ? 'open' : e.outcome ? 'shipped' : 'missed',
    ]),
  );
  return (
    <Stack space="space.100">
      <Text>
        {board.graded} graded, {board.open} open. Brier score (lower is better): model{' '}
        <Strong>{board.model.brier == null ? '-' : String(board.model.brier)}</Strong> over {board.model.n}, people{' '}
        <Strong>{board.human.brier == null ? '-' : String(board.human.brier)}</Strong> over {board.human.n}.
      </Text>
      {board.recent.length ? <DynamicTable head={t.head} rows={t.rows} /> : <Text>No forecasts recorded yet.</Text>}
    </Stack>
  );
}

function App() {
  const context = useProductContext();
  const projectKey = context && context.extension && context.extension.project && context.extension.project.key;
  const [target, setTarget] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [yourProbability, setYourProbability] = useState('');
  const [res, setRes] = useState(null);
  const [cal, setCal] = useState(null);
  const [board, setBoard] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!projectKey) return;
    invoke('calibration', { scope: projectKey }).then(setCal);
    invoke('scoreboard', {}).then(setBoard);
  }, [projectKey]);

  const run = async (name) => {
    setBusy(true);
    const out = await invoke(name, { scope: projectKey, target, targetDate, yourProbability });
    setRes(out);
    if (name === 'record') invoke('scoreboard', {}).then(setBoard);
    setBusy(false);
  };

  return (
    <Stack space="space.300">
      <Stack space="space.100">
        <Heading as="h2">Ship Odds</Heading>
        <Text>
          The odds of finishing on time, from this project's own throughput, and a record of how often those odds came true.
        </Text>
      </Stack>
      <Box>
        <Stack space="space.100">
          <Textfield placeholder="What has to ship: version name, epic key, or JQL" value={target} onChange={(e) => setTarget(e.target.value)} />
          <Textfield placeholder="Target date, YYYY-MM-DD" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} />
          <Textfield placeholder="Your own odds, e.g. 70 (optional, for the scoreboard)" value={yourProbability} onChange={(e) => setYourProbability(e.target.value)} />
          <Inline space="space.100">
            <Button appearance="primary" isDisabled={busy} onClick={() => run('forecast')}>Forecast</Button>
            <Button isDisabled={busy} onClick={() => run('record')}>Forecast and record</Button>
          </Inline>
        </Stack>
      </Box>
      {busy ? <Spinner /> : <Result res={res} />}
      <Stack space="space.100">
        <Heading as="h3">How often were its odds right here?</Heading>
        <Calibration cal={cal} />
      </Stack>
      <Stack space="space.100">
        <Heading as="h3">Scoreboard</Heading>
        <Scoreboard board={board} />
      </Stack>
    </Stack>
  );
}

ForgeReconciler.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
