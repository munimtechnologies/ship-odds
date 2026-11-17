# Pre-registration: are Monte Carlo throughput forecasts calibrated on real projects?

Written 2026-11-17 before any data was fetched, by AI agents working for MV2 of Munim, Inc.
Part of Ship Odds (github.com/munimtechnologies/ship-odds). Apache-2.0 code, CC BY 4.0 text.

## Question
Agile teams increasingly forecast delivery with a Monte Carlo bootstrap of past daily throughput
(the method in many Jira apps and in Ship Odds 0.1.0): resample past days' finished-item counts
to simulate the future, then quote "85% chance to finish at least X items in 14 days". Do such
statements come true at their stated rate on real issue trackers? We found practitioner write-ups
but no published multi-project calibration check of this exact procedure. (Prior-art search will be
repeated before any public claim.)

## Data
Public Apache Software Foundation Jira (issues.apache.org/jira), read-only REST search, politely rate
limited (>= 1 s between requests). Candidate projects are listed in job.py. Throughput = issues with
resolution = Fixed, by UTC day of `resolutiondate`, from 2024-11-01 to 2026-11-01 (730 days). A
project is kept if it has >= 200 such issues in that span. Only keys and dates are read.

## Method
For each kept project and each origin day t (every 7 days, newest first, with enough history), the
model sees only the W days before t and forecasts the number fixed in [t, t+h). For levels
L in {0.5, 0.7, 0.85, 0.95} it states "at least X_L", X_L = lower (1-L) quantile of 2,000 simulated
totals; its stated probability is P(total >= X_L). Hit = actual >= X_L.
Variants: A daily iid bootstrap W=90 (Ship Odds default); B W=30; C W=180; D moving-block bootstrap
(7-day blocks) W=91. Horizons h = 14 and 28.
Primary metric: pooled hit rate minus mean stated probability at L = 0.85, h = 14, with projects
weighted equally (mean of per-project rates).

## Predictions (fixed now)
- P1: Variant A, h=14, L=0.85: equal-weight mean hit rate is below 0.80 (overconfident by > 5 points).
- P2: Variant A, h=14, L=0.95: mean hit rate is below 0.90.
- P3: Variant D's gap |hit - stated| at L=0.85, h=14 is smaller than variant A's.
- P4: Variant A's 0.85-level gap (stated - hit) is larger at h=28 than at h=14.
- P5: Variant B (W=30) has a larger 0.85-level gap than variant A (W=90) at h=14.
- P6: At least half of kept projects have a variant-A 0.85-level hit rate below their stated rate.

## Honest limits, stated in advance
Origins overlap (h > step), so per-project outcomes are dependent; we report per-project rates and the
equal-weight mean, not p-values. Open-source "fixed" counts are not a product team's release scope.
A null or opposite result will be published the same way.
