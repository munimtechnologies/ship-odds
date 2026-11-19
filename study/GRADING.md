# Grading of the two pre-registered Apache studies (2026-11-19)

Graded on 2026-11-19 by AI agents working for MV2 of Munim, Inc. Each prediction is graded exactly as
written in `calib-apache/PREREGISTRATION.md` and `recal-apache/PREREGISTRATION.md` (both committed
on 2026-11-17, before any data was fetched). No threshold, metric or project filter was changed after the data
was seen. No human expert has checked this grading yet.

## Where and how it ran

- Machine: MV2's Windows desktop (the Dell), Python 3.11.9, standard library only, code exactly as tagged
  `v0.2.1` in this repo (files downloaded from GitHub; unit tests passed before the jobs ran).
- Run on 2026-11-18. Part 1 took about 4.8 minutes and part 2 about 3.2 minutes. No project failed to fetch.
- Data: public Apache Software Foundation Jira, issues resolved as Fixed between 2024-11-01 and 2026-11-01,
  counted per UTC day. 50 candidate projects (listed in `job.py`); **25 had at least 200 such issues and were
  kept** (AMQ, ARTEMIS, CALCITE, CAMEL, CASSANDRA, FINERACT, FLINK, HADOOP, HBASE, HIVE, HUDI, IGNITE, IMPALA,
  KAFKA, NIFI, OAK, OFBIZ, ORC, PDFBOX, PHOENIX, SLING, SOLR, SPARK, THRIFT, TIKA). Earlier text in this repo said
  "about 50 projects"; that was the candidate list, and the kept set is 25.
- Raw outputs: `calib-apache/RESULTS.md`, `calib-apache/results.json`, `calib-apache/data/daily_counts.json`;
  `recal-apache/RESULTS.md`, `recal-apache/results.json`, `recal-apache/data/apache_fixed_20241101_20261101.json`.
- The same two jobs are also queued on a sealed Linux container (seed 7, same code). When they finish they will be
  reported here as a reproduction.

## Part 1: are Monte Carlo throughput odds calibrated?

Primary number (variant A, daily bootstrap of the last 90 days, 14-day horizon, the 85% level): the model's
statements carried a mean stated probability of **0.8824** and came true **0.7998** of the time
(equal-weight mean over 25 projects). 23 of 25 projects (0.92) were below their stated rate.

| Prediction | Value | Verdict |
|---|---|---|
| P1: A, h=14, 85% level: mean hit rate below 0.80 | 0.7998 | **held** (by 0.0002, so only just) |
| P2: A, h=14, 95% level: mean hit rate below 0.90 | 0.9047 | **failed** |
| P3: block bootstrap (D) gap smaller than A's | D 0.0590 vs A 0.0827 | **held** |
| P4: A's 85% gap larger at h=28 than at h=14 | 0.1183 vs 0.0827 | **held** |
| P5: 30-day window (B) gap larger than 90-day (A) | B 0.0711 vs A 0.0827 | **failed** (the opposite: the 30-day window was a little better) |
| P6: at least half of projects below their stated rate | 0.92 | **held** |

Four of six held. At 28 days the 85% statements came true 0.7509 of the time and the 95% statements 0.8510.

**Control.** On 10 synthetic projects whose days really are independent draws from a fixed distribution (the
model's own assumption), the same 85% statements had a mean stated probability of 0.8779 and came true 0.8489 of
the time. So the method overstates by about 3 points even when the past is a perfect guide (it treats 90 days of
noisy history as the exact future rate). On the real projects it overstates by about 8 points. Roughly the
other 5 points come from real teams' pace changing over time. The 3-point estimate is from only 10 synthetic
projects and is approximate.

## Part 2: can the forecaster correct itself from its own record?

The correction (PIT recalibration, shrunk toward no change with 10 pseudo-observations, learned only from the
same project's earlier forecasts whose outcome was already known) was evaluated on the origins that had at least
12 such earlier forecasts. That is why part 2's raw hit rate (0.7934) differs a little from part 1's (0.7998).

| Prediction | Raw | Corrected | Verdict |
|---|---|---|---|
| R1 (primary): h=14, 85% level, gap \|stated - hit\| smaller | 0.0890 | 0.0443 | **held** |
| R2: h=14, 85% level, corrected hit rate in [0.80, 0.90] | (0.7934) | 0.8465 | **held** |
| R3: h=14, mean Brier score lower | 0.18223 | 0.18075 | **held** (a small gain: 0.0015) |
| R4: h=28, 85% level, gap smaller | 0.1294 | 0.0659 | **held** |
| R5: h=14, at least 60% of projects have a lower Brier score | | 0.32 (8 of 25) | **failed** |

Four of five held. The corrected 85% statements came true 0.8465 of the time at 14 days (stated 0.8908) and
0.8122 at 28 days (raw 0.7400). The corrected 95% statements came true 0.9314 at 14 days (raw 0.8972).

The price is sharpness: the corrected 85% "at least X items" count is on average 0.8619 of the raw one (14% fewer
items promised).

**Exploratory (no predictions):** with the block bootstrap (variant D), the correction moved the 85% hit rate
from 0.8170 to 0.8567, but the Brier score got slightly worse (0.17249 to 0.17398). At 28 days the Brier score
also got slightly worse (0.20935 to 0.21024) even though the 85% gap halved.

**Where the Brier gain comes from.** The 8 projects whose Brier score improved at 14 days include the four with
the largest gains: HUDI (0.3427 to 0.2548), AMQ (0.1780 to 0.1530), ORC (0.2389 to 0.2209) and KAFKA (0.2232 to
0.2179). These are projects where the raw model was badly off (for HUDI, its 85% statements came true 0.47 of
the time). On most of the other 17 projects the correction added a small amount of noise (for example SOLR 0.1703
to 0.1820, HIVE 0.1632 to 0.1735). So the average Brier gain is real but is carried by a few badly miscalibrated
projects.

**Controls behaved as designed.** On 8 synthetic stable projects the correction changed little at the 85% level
(hit 0.8685 to 0.8864) but made the Brier score worse on all 8 (0.14668 to 0.15336): correcting a model that is
not wrong costs accuracy. On 8 synthetic projects whose pace drifts down, it lifted the 85% hit rate from 0.6688
to 0.8149 and improved the Brier score on all 8 (0.24732 to 0.21735).

## What this means for Ship Odds

1. The common "85% date" from a throughput Monte Carlo was too optimistic on these open-source projects: 80% at
   two weeks, 75% at four weeks, with 23 of 25 projects below the stated rate.
2. Learning from each project's own record fixes the **coverage** of the 85% and 95% statements on average
   (84.7% and 93.1% at two weeks). That is the number a team promises a customer, so Ship Odds keeps the corrected
   85% and 95% dates.
3. It does **not** make the probability for a single date more accurate on most projects. It helps a lot where the
   raw model is badly off and costs a little where it is not. The next step is a rule that applies the correction
   only when a project's own record shows a clear miss. That rule will be pre-registered and tested on projects and
   trackers not used here, because it was suggested by these data.

## Limits

Forecast origins overlap (every 7 days, 14- or 28-day horizons), so outcomes within a project are dependent. We
report equal-weight means and per-project values, not p-values. The 25 projects are large Apache open-source
projects whose "Fixed" counts are not a product team's release scope. P1 held by 0.0002, which is well within
noise; read it as "about 80%", not as "below 80%". All of this work was carried out with AI agents working for
MV2 of Munim, Inc.

Text: CC BY 4.0. Code: Apache-2.0.
