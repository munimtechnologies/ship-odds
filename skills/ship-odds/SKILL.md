---
name: ship-odds
description: Answer "will this Jira version, epic or query ship by date X?" with probabilities from the team's own finished work, corrected by how often such odds came true for that team before. Use when a user asks for delivery odds, a realistic ship date, whether to trust a forecast, or to log a forecast for later scoring, and the Ship Odds MCP server for their Atlassian site is connected.
license: Apache-2.0
---

# Ship Odds: delivery odds for Jira that correct themselves

Ship Odds is a Forge app for Jira Cloud (github.com/munimtechnologies/ship-odds, Apache-2.0, by MV2 of Munim, Inc., written with AI agents). Its MCP tools are served by Atlassian at `https://mcp.atlassian.com/forge/<appId>` once a site admin installs the app and turns the tools on (Atlassian Administration > Apps > Sites > your site > Connected apps > Ship Odds). Sign-in is Atlassian's OAuth consent screen; every call runs with the signed-in user's own Jira permissions. The tools only read Jira.

## Tools

| Tool | Use it for | Inputs |
|---|---|---|
| `ship-odds-forecast` | Odds of finishing a target by a date, plus 50/85/95% dates | `target` (version name such as `2.4`, epic key such as `ENG-120`, or JQL), `targetDate` (YYYY-MM-DD), optional `scope` (project key or JQL that sets the pace), optional `windowDays` (14 to 365, default 90) |
| `ship-odds-calibration` | "Can I trust these numbers?" How often the raw model's odds came true on this project's past year | optional `scope`, `windowDays`, `horizonDays` (7 to 56, default 14) |
| `ship-odds-scoreboard` | Recorded forecasts and Brier scores for the raw model, the corrected model and people | none |

## How to answer

1. Turn relative dates ("end of next sprint", "Friday") into YYYY-MM-DD yourself and say which date you used. If the target or the date is missing, ask once.
2. Call `ship-odds-forecast`. If the result has `corrected`, lead with `corrected.probability` and `corrected.dates`, then give the raw `probability` in one clause. Explain the difference with `corrected.basedOn.slowTail`: the share of the project's past forecasts in which the team landed in the model's slowest 15% (15% would be calibrated). A corrected date of `null` means "later than the simulation reached": say so, never invent a date.
3. If there is no `corrected`, give the raw numbers and say they are not yet corrected (less than about 12 replayable past forecasts, or too much history to read; see `warnings`).
4. Mention `remaining` (open items) and `throughputPerWeek`, and pass on `assumptions` in one sentence.
5. Before someone promises a date to a customer, call `ship-odds-calibration` and quote its `summary`.

## Rules

- Every number must come from a tool result. Never round a probability up.
- A forecast is not a promise: new scope, team changes or very uneven item sizes change it.
- On an error, explain it plainly (an unknown version name, a JQL typo, a date in the past) and suggest the fix.

## Example

User: "Will 2.4 ship by the end of the month?"
Call `ship-odds-forecast` with `{"target": "2.4", "targetDate": "2026-12-31"}`.
Answer: "62% by 31 Dec once corrected for this project's track record (the uncorrected model says 81%; in 9 of the last 38 replayed forecasts the team landed in the model's slowest 15%). Corrected 85% date: 12 Jan. 34 items are open; the team finishes about 9 a week."
(Numbers illustrative.)
