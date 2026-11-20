# Grading of the pre-registered Ship Odds studies

Parts 1 and 2 were graded on 2026-11-19 and part 3 on 2026-11-20, by AI agents working for MV2 of Munim, Inc.
Each prediction is graded exactly as written in `calib-apache/PREREGISTRATION.md`, `recal-apache/PREREGISTRATION.md`
(both committed on 2026-11-17, before any data was fetched) and `replicate-trackers/PREREGISTRATION.md` (committed
on 2026-11-19 at 08:44 UTC, before any of its data was fetched). No threshold, metric or project filter was changed
after the data was seen. No human expert has checked this grading yet.

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

## Part 3: replication on four other trackers, and a gated correction

- Run on 2026-11-19 on the Dell (Python 3.11.9, about 15 minutes), with the code committed alongside the
  pre-registration (`replicate-trackers/replicate.py`, `job.py`; unit tests passed first). The run first checked
  that the pre-registration was public on GitHub, then fetched.
- Data: public Jira trackers of MongoDB, Atlassian, Jenkins and Red Hat, 2024-11-01 to 2026-11-01, keys and
  resolution dates only. 47 candidate projects; **28 kept** (10 MongoDB, 8 Atlassian, 1 Jenkins, 9 Red Hat):
  mongodb SERVER, WT, PYTHON, JAVA, NODE, CSHARP, CDRIVER, RUST, COMPASS, MONGOSH; atlassian JRACLOUD, CONFCLOUD,
  JSDCLOUD, JRASERVER, JSWSERVER, CONFSERVER, JSDSERVER, BSERV; jenkins JENKINS; redhat WFLY, WFCORE, RESTEASY,
  ELY, JBEAP, OCPBUGS, RHEL, ACM, MTV. Dropped as written in the pre-registration: two keys that do not exist on
  their tracker (mongodb DOCS, jenkins INFRA), redhat CNV (more than 20,000 issues), three Red Hat projects for
  which the anonymous search returned no issues (ISPN, OSDOCS, AAP) and 13 projects under 200 issues.
- Raw outputs: `replicate-trackers/RESULTS.md`, `replicate-trackers/results.json`, `replicate-trackers/run.log`,
  `replicate-trackers/data/trackers_fixed_20241101_20261101.json`.
- Check of the code: on part 2's Apache data, part 3's code gave exactly part 2's raw and corrected Brier scores
  (0.18223 and 0.18075), as its unit test requires.

| Prediction (h=14, 85% level, 28 projects, equal weight) | Value | Verdict |
|---|---|---|
| T1: raw stated - hit > 0.03 | 0.8908 - 0.8363 = 0.0545 | **held** |
| T2: at least half of projects below their stated rate | 0.8214 (23 of 28) | **held** |
| T3: raw gap larger at h=28 than at h=14 | 0.0698 vs 0.0545 | **held** |
| T4: always-corrected \|gap\| smaller than raw | 0.0313 vs 0.0545 | **held** |
| T5 (primary for the gate): gated Brier lower than always-corrected | 0.16365 vs 0.16691 | **held** |
| T6: gated Brier lower than raw | 0.16365 vs 0.16219 | **failed** |
| T7: gated \|gap\| smaller than raw | 0.0516 vs 0.0545 | **held** |

Six of seven held. The pre-registration said Ship Odds adopts the gate only if T5 **and** T6 hold. T6 failed, so
**the gate is not adopted.**

**What replicated.** The raw "85%" statements were too optimistic on product-company trackers too: they came true
0.8363 of the time at 14 days (stated 0.8908) and 0.8014 at 28 days (stated 0.8712). By tracker at 14 days:
MongoDB 0.8065 (all 10 projects below their stated rate), Atlassian 0.8523, Red Hat 0.8514, Jenkins 0.8701 (one
project). The gap is smaller than on Apache (0.0545 against 0.0890 on the same code), but it is in the same
direction and grows with the horizon. The always-on correction again moved the 85% hit rate toward its claim
(0.8363 to 0.8664; at 28 days 0.8014 to 0.8469).

**What did not.** On these trackers no correction improved the probabilities on average. Mean Brier scores at 14
days: raw 0.16219, always-corrected 0.16691, gated 0.16365, k40 (stronger shrinkage, exploratory) 0.16369. The
always-on correction lowered the Brier score on only 4 of 28 projects (mongodb PYTHON, NODE, CDRIVER and atlassian
CONFSERVER) and raised it on 24; at 28 days the mean also got worse (0.18142 to 0.19112). Part 2's small Brier
gain on Apache (R3) therefore did not replicate.

**Why the gate could not rescue it.** The gate never opened on 17 of the 28 projects, so there it simply returned
the raw forecast. On the 11 projects where it opened at least once, correcting made the Brier score worse on 10
and better only on mongodb PYTHON (0.21668 to 0.21004). The clearest case is redhat WFLY: the gate was open for
0.78 of its forecasts and its Brier score went from 0.19533 to 0.21572. A project whose recent forecasts missed in
one direction did not keep missing the same way over the next weeks often enough for the correction to pay. This is
our reading of the numbers, not a separate test.

**Controls.** On 8 synthetic stable projects the gate was open for 0.0114 of forecasts and the gated Brier score
(0.14733) stayed close to raw (0.14668), while always correcting cost more (0.15336). On 8 synthetic projects whose
pace drifts down, the gate opened for 0.4838 of forecasts and improved the Brier score on all 8 (0.24732 to
0.23223). So the gate works as built; real teams just did not show persistent drift of that kind.

## What this means for Ship Odds

1. The common "85% date" from a throughput Monte Carlo was too optimistic: on 23 of 25 Apache projects and on 23
   of 28 projects on four other trackers (46 of 53), its 85% statements came true less often than stated, and more
   so at four weeks than at two.
2. Learning from each project's own record fixes the **coverage** of the 85% statement on average, on both data
   sets (Apache 0.7934 to 0.8465; other trackers 0.8363 to 0.8664). That is the date a team promises a customer, so
   Ship Odds keeps the corrected 85% and 95% dates as its **promise dates**.
3. It does **not** make the probability for a single date more accurate: the Brier score improved on 8 of 25 Apache
   projects and 4 of 28 others. From 0.2.3 on, Ship Odds therefore shows the **raw** odds as its headline
   probability for a date, with the corrected odds next to them, and the scoreboard keeps checking both live.
4. The gated correction is not adopted (T6 failed).

## Limits

Forecast origins overlap (every 7 days, 14- or 28-day horizons), so outcomes within a project are dependent. We
report equal-weight means and per-project values, not p-values. The Apache projects are open-source projects whose
"Fixed" counts are not a product team's release scope; the other trackers show only public issues (for Atlassian,
mostly customer-reported bugs), and Jenkins contributes one project. P1 held by 0.0002, which is well within
noise; read it as "about 80%", not as "below 80%". The gate's constants were chosen after seeing part 2, which is
why it was graded only on new trackers. All of this work was carried out with AI agents working for MV2 of
Munim, Inc.

Text: CC BY 4.0. Code: Apache-2.0.
