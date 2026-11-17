# Ship Odds

**Jira delivery odds that correct themselves.**

Ship Odds answers "will we make the date?" with a probability computed from your own team's finished work. Then it does something forecasting tools don't: it replays the same model on your past year, sees how often its odds came true *for your team*, and **corrects today's odds and dates by that record**. If your team has landed in the model's slowest 15% far more often than 15% of the time, the corrected "85% date" moves later until it reflects that.

Most delivery forecasters sell an "85% date". Some now show whether those dates came true. Ship Odds also uses that record to fix the number you are about to promise a customer.

It is a [Forge](https://developer.atlassian.com/platform/forge/) app for Jira Cloud with:

- a **Jira project page**: type a version name, epic key or JQL and a date, and get the corrected odds and 50% / 85% / 95% dates, next to the raw model's;
- a **Rovo agent** ("Ship Odds") that answers in chat: *"What are the odds we finish 2.4 by 12 December?"*, *"How often have your forecasts been right for this project?"*;
- **MCP tools** (Forge `rovo:mcp`), so the forecast, calibration and scoreboard can be used from Rovo Studio agents or from MCP clients such as Claude Code, Cursor or Codex, once a site admin turns them on. [`skills/ship-odds/SKILL.md`](skills/ship-odds/SKILL.md) tells a coding agent how to use them;
- a **scoreboard**: record a forecast, optionally with your own guess ("I think 70%"). After the target date it is graded automatically, and the raw model, the corrected model and the people get Brier scores, so the correction is checked live too.

Status: **0.2.1, not yet deployed to a live Jira site.** The forecasting, correction, hindcast, JQL and grading logic is covered by automated tests against a fake Jira (`npm test`, or `python -m unittest test_ship_odds`). On 2026-11-17 the 0.2.0 code was installed from npm on a Windows machine with Node 24, and all 33 JavaScript tests passed there. 0.2.1 pins every dependency to an exact version, so the build is reproducible. The Forge UI and Rovo wiring still have to be tried on a real developer site; this README will say when they have been.

## How it works

1. **Throughput.** Ship Odds reads the items in the scope (a project, or any JQL) that were finished in the past year. The forecast samples the last 90 days (adjustable from 14 to 365): how many finished on each UTC day, including the days when nothing finished.
2. **Monte Carlo.** It counts the target's open items, then simulates 10,000 futures. Each simulated day's throughput is drawn at random from those past days. The raw odds are the share of futures that finish by the target date; the 50/85/95% dates are percentiles of the finish day.
3. **Replay.** Every 7 days back through the past year, it gives the same model only the 90 days before that point and asks how many items will finish over the next *h* days, where *h* is the time to your target date (7 to 56 days). It records where the real outcome fell in the model's range: the probability integral transform, or PIT. A calibrated model's PITs are spread evenly from 0 to 1. A team whose pace keeps slipping piles them up near 0.
4. **Correction.** From those PITs it builds a recalibration map *G* (their empirical distribution, shrunk toward "no change" with 10 pseudo-observations, so a short history corrects only a little), and turns each raw probability *p* into **1 − G(1 − p)**. This is the standard recalibration of a predictive distribution (Gneiting et al. 2007; Kuleshov et al. 2018, "Accurate uncertainties for deep learning using calibrated regression"), applied here to delivery forecasts. The corrected dates are the first days whose corrected odds reach 50%, 85% and 95%. If the corrected odds never reach a level within the simulated range, the date is shown as "later than the simulation reached" rather than made up. It needs at least 12 replayed forecasts; with less history you get the raw odds and a note.
5. **Track record table.** The calibration view shows how often the raw model's stated "at least X items" came true at 50%, 70%, 85% and 95% (made-up numbers below). The corrected odds are learned from this record.

   | Odds the raw model gave | How often it came true | Verdict |
   |---|---|---|
   | 86% | 61% (42% to 77%) | overconfident |

6. **Scoreboard.** A recorded forecast stores the open issue keys, the raw odds and the corrected odds. The day after the target date, a daily job checks whether all of those issues were finished by the end of that date (UTC). The outcome is 1 or 0. The Brier score is the mean of (probability - outcome)²: 0 is perfect, and 0.25 is what always saying 50% earns.

## Does the correction actually help?

That is an empirical question, so it is being tested in the open rather than assumed. [`study/calib-apache/`](study/calib-apache/) is a pre-registered study on about 50 public Apache Software Foundation Jira projects. Part 1 asks whether the raw model's odds come true at their stated rate. Part 2 ([`study/recal-apache/`](study/recal-apache/)) asks whether the correction above, learned only from each project's own past (out of sample, forecast by forecast), brings the 85% statements closer to 85% and lowers the Brier score. Both sets of predictions were written down before any data was fetched. Results will be committed as they are, whichever way they go.

## Assumptions and limits

- The next weeks are assumed to look like the sampled window: similar team, similar item sizes, no big holidays. Ship Odds counts items and ignores story points on purpose, so it needs no estimates.
- The correction assumes the team will miss (or beat) the model in the same way it did over the past year. A team that has just changed a lot breaks that assumption. The correction is learned at the target's horizon and applied to every date in the range, which is an approximation for dates far from the target.
- Items added to the target after a forecast are not in it. The scoreboard grades the items that existed when the forecast was made.
- "Finished" means in the status category Done. The date used is the **resolution date**; for items without a resolution (workflows that never set one) it is the date the item entered the Done category. Resolution comes first because it survives CSV imports and migrations. Days are UTC days.
- Reads at most 5,000 finished items and 1,000 open items per request. If more than 5,000 items finished in the past year, the forecast uses the window only and is not corrected; it says so.
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

Forge CLI 15 needs Node.js 22.23.4 or newer, or 24.22.1 or newer.

To use the MCP tools from outside Rovo, a site admin turns them on under **Atlassian Administration > Apps > Sites > (site) > Connected apps > Ship Odds > Tools**. The endpoint is `https://mcp.atlassian.com/forge/<appId>` (the UUID at the end of `app.id` in `manifest.yml`).

## Demo data from a real project (`demo/`)

A forecasting app needs history to show anything, and a fresh developer site has none. `demo/apache_demo.py` builds a demo project from a **public Apache Jira project** instead of made-up numbers:

1. `python demo/apache_demo.py fetch --out-dir out` picks a project and a fix version released in 2026, takes the moment 28 days before that release (the cutoff), and saves the year of issues resolved as Fixed before the cutoff plus the version's issues that were still open at the cutoff. It also saves what Ship Odds' model would have said at the cutoff, and what really happened afterwards.
2. `python demo/apache_demo.py csv --raw out/demo_raw.json --anchor YYYY-MM-DD --out demo.csv` moves every date forward by the same number of days so the cutoff becomes the import day, and writes a CSV for Jira's admin CSV importer. Map both **Resolution** and **Resolved** (Date Resolved), or Jira drops the resolution dates; the date format is `yyyy-MM-dd HH:mm`.

Every imported issue links back to its Apache original and says the dates were moved. One limit: Apache assigns fix versions in hindsight, so the "open at the cutoff" set is what eventually shipped in that version, not what the team planned at the time.

**First run (2026-11-17).** The script chose Apache Solr, fix version 10.1: 421 issues finished in the year before the cutoff (2026-09-28), and 27 of the version's issues were still open at the cutoff. The raw model gave 96% odds that all 27 would be done by the release day (2026-10-26). In fact 25 were, and the last 2 were finished 4 days later, on 2026-10-30. A single forecast proves nothing either way. Telling a well-calibrated 96% from an overconfident one takes many forecasts, which is why the study above exists.

## Tests

```sh
npm test                                     # node --test, no dependencies needed
python -m unittest test_ship_odds            # the same, plus manifest and package checks
python -m unittest demo/test_apache_demo.py  # demo builder, offline
```

## About

Built by MV2 of Munim, Inc. (mv2@munimtech.com) as an entry to Atlassian's Codegeist 2026 hackathon. The code was written with AI agents working in his name and checked by the automated tests above.

Licence: Apache-2.0 (see LICENSE). It uses Atlassian's Forge packages (`@forge/*`) and React (MIT). Demo issue titles come from the Apache Software Foundation's public Jira.
