# Ship Odds

**Jira delivery forecasts that grade themselves.**

Ship Odds answers "will we make the date?" with a probability computed from your own team's finished work. It also shows how often those probabilities came true on your own history. Most forecasting tools give you an "85% date" and never check whether their 85% dates arrive 85% of the time. Ship Odds does that check, the day you install it.

It is a [Forge](https://developer.atlassian.com/platform/forge/) app for Jira Cloud with:

- a **Jira project page**: type a version name, epic key or JQL and a date, and get the odds plus the 50% / 85% / 95% finish dates;
- a **Rovo agent** ("Ship Odds") that answers in chat: *"What are the odds we finish 2.4 by 12 December?"*, *"How often have your forecasts been right for this project?"*;
- **MCP tools** (Forge `rovo:mcp`), so the same forecast and calibration actions can be used from Rovo Studio agents or from MCP clients such as Claude Code, once a site admin turns them on;
- a **scoreboard**: record a forecast, optionally with your own guess ("I think 70%"). After the target date it is graded automatically, and the model and the people get Brier scores.

Status: **0.1.0, not yet deployed to a live Jira site.** The forecasting, hindcast, JQL and grading logic is covered by automated tests against a fake Jira (`npm test`, or `python -m unittest test_ship_odds`). The Forge UI and Rovo wiring still have to be tried on a real developer site; this README will say when they have been.

## How it works

1. **Throughput.** Ship Odds reads the items in the scope (a project, or any JQL) that reached a Done status in the last 90 days (adjustable from 14 to 365). It counts how many finished on each UTC day, including the days when nothing finished.
2. **Monte Carlo.** It counts the target's open items, then simulates 10,000 futures. Each simulated day's throughput is drawn at random from those past days. The odds are the share of futures that finish by the target date; the 50/85/95% dates are percentiles of the finish day.
3. **Hindcast (the track record).** It replays the same model on the past year. Every 7 days it gives the model only the 90 days before that point, asks it "how many items will finish in the next 14 days?", and records its stated "at least X items" for the 50%, 70%, 85% and 95% levels. Then it checks what actually happened. You get a table like this one (made-up numbers):

   | Odds the model gave | How often it came true | Verdict |
   |---|---|---|
   | 86% | 61% (42% to 77%) | overconfident |

   If it says *overconfident*, discount its odds for this team. The replayed windows overlap, so the ranges are a rough guide, not a formal test.
4. **Scoreboard.** A recorded forecast stores the open issue keys at that moment. The day after the target date, a daily job checks whether all of those issues were Done by the end of that date (UTC). The outcome is 1 or 0. The Brier score is the mean of (probability - outcome)²: 0 is perfect, and 0.25 is what always saying 50% earns.

## Assumptions and limits

- The next weeks are assumed to look like the sampled window: similar team, similar item sizes, no big holidays. Ship Odds counts items and ignores story points on purpose, so it needs no estimates. If your items vary a lot in size, the hindcast will show up as poor calibration.
- Items added to the target after a forecast are not in it. The scoreboard grades the items that existed when the forecast was made.
- "Done" means the status category Done. The date used is the status-category change date, or the resolution date if that is missing. Days are UTC days.
- Reads at most 5,000 finished items and 1,000 open items per request, and says so when it hits a limit.
- Deleted issues count as done when a forecast is graded.

## Permissions and data

- Scopes: `read:jira-work` (read issues) and `storage:app` (the forecast log). It never writes to Jira.
- Forecasts and calibration run **as the person asking**, so nobody sees numbers built from issues they can't browse. Only the daily grading job runs as the app.
- No data leaves Atlassian: no external calls, no analytics. The forecast log lives in the app's Forge storage on your site.

## Install (developers)

```sh
npm install
forge register      # gives the app its own id in manifest.yml
forge deploy
forge install       # pick your Jira site
```

To use the MCP tools from outside Rovo, a site admin turns them on under **Atlassian Administration > Apps > Sites > (site) > Connected apps > Ship Odds > Tools**. The endpoint is `https://mcp.atlassian.com/forge/<appId>`.

## Tests

```sh
npm test                        # node --test, no dependencies needed
python -m unittest test_ship_odds  # the same, plus manifest checks
```

## About

Built by MV2 of Munim, Inc. (mv2@munimtech.com) as an entry to Atlassian's Codegeist 2026 hackathon. The code was written with AI agents working in his name and checked by the automated tests above.

Licence: Apache-2.0 (see LICENSE). It uses Atlassian's Forge packages (`@forge/*`) and React (MIT).
