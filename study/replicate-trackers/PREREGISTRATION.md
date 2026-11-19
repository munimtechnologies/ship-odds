# Pre-registration, part 3: do the Apache findings replicate on other trackers, and does a gated correction beat always correcting?

Written 2026-11-19, before any data from the trackers below was fetched for this study, by AI agents working for
MV2 of Munim, Inc. Part of Ship Odds (github.com/munimtechnologies/ship-odds). Apache-2.0 code, CC BY 4.0 text.
On 2026-11-19 we made one request per tracker, each asking for a single issue, only to check that anonymous
search works (MongoDB, Atlassian, Jenkins and Red Hat answered; OpenJDK's tracker refused). Those checks showed issue
totals since 2024-11-01 for MongoDB SERVER, Atlassian JRACLOUD and Jenkins JENKINS (counts only, no dates per day).
They were not used to choose projects or thresholds.

## Why
Parts 1 and 2 (graded in `../GRADING.md`) found, on 25 Apache projects, that Monte Carlo throughput "85%"
statements came true about 80% of the time at 14 days, and that PIT self-correction brought that to 84.7%.
However, the correction improved the Brier score on only 8 of 25 projects. The gain came from a few badly
miscalibrated projects. Two questions follow:
1. **Replication.** Do these findings hold on trackers we have not looked at, including product companies
   (MongoDB, Atlassian, Red Hat) rather than only open-source foundations?
2. **A gated correction.** The rule below applies the correction only when a project's own record shows a clear
   miss. It was suggested by part 2's data (that is why it is tested here, on new data only). Its constants were
   set from part 2 and are fixed now.

## Data
Public, anonymous Jira search APIs, issues with the listed resolution, by UTC day of `resolutiondate`,
2024-11-01 to 2026-11-01 (730 days). Only keys and dates are read, with at least 1 s between requests.
- MongoDB (jira.mongodb.org, resolution Fixed): SERVER, WT, TOOLS, PYTHON, JAVA, NODE, CSHARP, GODRIVER, CDRIVER,
  CXX, RUST, PHPLIB, PHPC, RUBY, MOTOR, COMPASS, MONGOSH, DOCS, SPARK, KAFKA.
- Atlassian (jira.atlassian.com, resolution Fixed): JRACLOUD, JSWCLOUD, CONFCLOUD, JSDCLOUD, BCLOUD, JRASERVER,
  JSWSERVER, CONFSERVER, JSDSERVER, BSERV.
- Jenkins (issues.jenkins.io, resolution Fixed): JENKINS, INFRA.
- Red Hat (redhat.atlassian.net, resolution Done): WFLY, WFCORE, UNDERTOW, RESTEASY, ISPN, JGRP, ELY, JBEAP,
  OCPBUGS, RHEL, CNV, ACM, OSDOCS, MTV, AAP.
A project is kept if it has at least 200 such issues in the span. Projects that are not public, or that fail to
fetch, are listed and dropped. Projects with more than 20,000 matching issues are excluded rather than truncated.
If fewer than 10 projects are kept, the study is reported as inconclusive and no prediction is graded.

## Method
Exactly part 2's prequential procedure (daily iid bootstrap of the 90 days before each origin, 2,000 runs, origins
every 7 days, levels 0.5/0.7/0.85/0.95, PIT recalibration from earlier origins whose horizon had ended, at most 365
days old, at least 12 of them, shrinkage k = 10, seed 7), at horizons 14 (primary) and 28 days. Four arms on the
same origins:
- **raw**: the Monte Carlo model.
- **cal**: always corrected (part 2's rule).
- **gated**: corrected only if the available PITs show a clear miss, and raw otherwise. Of the n available PITs,
  let s be the number at or below 0.15 and f the number at or above 0.85. The gate is open if
  P(Binomial(n, 0.15) >= s) < 0.001 or P(Binomial(n, 0.15) >= f) < 0.001 (exact).
- **k40** (exploratory, no prediction): always corrected, with stronger shrinkage (k = 40).
Projects enter a run's summary if they have at least 20 evaluated origins. All summaries weight projects equally.
Brier score: per origin and level, for the raw event "actual >= X_L", as in part 2.
Code: `replicate.py` (its raw and cal arms reproduce part 2's code exactly; a unit test checks this) and `job.py`.
Also reported, not graded: results per tracker; the same arms on part 2's Apache data (exploratory, since the gate
was suggested by those data); synthetic stable and drifting controls.

## Predictions (fixed now; h = 14 and the 0.85 level unless stated; equal-weight means over all kept projects)
- T1: the raw model is overconfident by more than its built-in 3 points: mean stated - mean hit > 0.03.
- T2: at least half of the kept projects have a raw hit rate below their stated rate.
- T3: the raw gap (stated - hit) is larger at h = 28 than at h = 14.
- T4: the always-corrected |gap| is smaller than the raw |gap| (replicates R1).
- T5 (primary for the gate): the gated arm's mean Brier score is lower than the always-corrected arm's.
- T6: the gated arm's mean Brier score is lower than the raw arm's.
- T7: the gated |gap| is smaller than the raw |gap|.

## Honest limits, stated in advance
Forecast origins overlap, so outcomes within a project are dependent. We report equal-weight means and per-project
values, not p-values. The trackers mix product teams and open-source communities, and public trackers show only
public issues (for Atlassian, mostly bugs reported by customers). The gate's constants (tail 0.15, level 0.001) were
chosen after seeing part 2. That is why it is graded only on these new trackers. A null or opposite result will be
published the same way, and Ship Odds will only adopt the gate if T5 and T6 hold.
