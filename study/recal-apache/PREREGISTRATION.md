# Pre-registration, part 2: can a delivery forecaster correct itself from its own track record?

Written 2026-11-17 (about 14:00 UTC), before any data for this study or for part 1 (`study/calib-apache/`) had been
fetched or seen, by AI agents working for MV2 of Munim, Inc. Part of Ship Odds
(github.com/munimtechnologies/ship-odds). Apache-2.0 code, CC BY 4.0 text.

## Question
Part 1 asks whether Monte Carlo throughput forecasts ("85% chance to finish at least X items in 14 days")
come true at their stated rate on real issue trackers. Part 2 asks the follow-up a team actually needs:
if a project's past forecasts were off, can the forecaster correct today's odds using only that project's
own past, so that its 85% statements come true about 85% of the time, without peeking at the future?

The correction is the one Ship Odds 0.2.0 ships: probability-integral-transform (PIT) recalibration
(Gneiting, Balabdaoui & Raftery 2007; Kuleshov, Fenner & Ermon 2018), shrunk toward no correction.
A prior-art search on 2026-11-17 found agile tools that *grade* forecasts by calibration (e.g. divim.io)
and a concept demo that learns slip across programs, but no Jira/agile forecasting tool or study that
recalibrates throughput Monte Carlo odds from each team's own PIT history, and no multi-project test of it.

## Data
Exactly part 1's data: public Apache Software Foundation Jira, issues with resolution = Fixed, by UTC day of
`resolutiondate`, 2024-11-01 to 2026-11-01 (730 days), same 50 candidate projects, kept if >= 200 such issues.
Read-only, >= 1 s between requests, only keys and dates.

## Method (prequential, strictly out of sample)
For each kept project, origins t every 7 days, in time order. At t the raw model (variant A of part 1:
daily iid bootstrap of the W = 90 days before t, 2,000 runs) simulates the number fixed in [t, t+h).
- Its PIT at t is F(a-1) + u(F(a) - F(a-1)) for the actual count a, with u uniform (seeded).
- Recalibration at t uses only PITs from earlier origins whose whole horizon had ended by t
  (t_j + h <= t) and that are at most 365 days old (as in the app). It needs >= 12 of them;
  origins with fewer are not evaluated. G(x) = (#{PIT <= x} + 10x) / (n + 10).
- For each level L in {0.5, 0.7, 0.85, 0.95}:
  raw statement "at least X_L", X_L = lower (1-L) quantile, stated p_raw = P(T >= X_L);
  corrected statement "at least Y_L", Y_L = the largest count whose corrected probability
  1 - G(F(Y-1)) is >= L, stated p_cal = that probability.
  Hit = actual >= X_L (raw) or >= Y_L (corrected).
- Brier, per origin and level, for the raw event "actual >= X_L": raw probability p_raw vs. corrected
  probability 1 - G(F(X_L - 1)) of the same event.
Projects enter a variant's summary if they have >= 20 evaluated origins. All summaries weight projects
equally (mean of per-project rates). Horizons h = 14 (primary) and 28. Exploratory, no predictions: the same
correction on part 1's variant D (7-day moving-block bootstrap, W = 91) at h = 14, and sharpness (mean
Y_0.85 / X_0.85, i.e. how much lower the corrected "at least" count is).

Sanity controls, reported alongside: synthetic iid Poisson projects (correction should change little) and
synthetic projects whose pace drifts down (correction should raise the 0.85 hit rate).

## Predictions (fixed now)
- R1 (primary): h = 14, L = 0.85: the corrected gap |mean stated - mean hit| is smaller than the raw gap,
  on the same evaluated origins.
- R2: h = 14, L = 0.85: the corrected mean hit rate is between 0.80 and 0.90.
- R3: h = 14: the mean Brier score (over projects; per project over origins and the 4 levels) is lower with
  corrected probabilities than with raw ones.
- R4: h = 28, L = 0.85: R1 holds.
- R5: h = 14: at least 60% of projects have a lower corrected Brier score than raw.

## Honest limits, stated in advance
Origins overlap (h > 7 days), so outcomes within a project are dependent; we report per-project values and
equal-weight means, not p-values. If part 1 finds the raw model already calibrated, R1 and R2 have little
room to hold and that will be said. The correction can only fix a miss that persists; a sudden change in a
team is outside what it can learn. Open-source "fixed" counts are not a product team's release scope.
A null or opposite result will be published the same way, and Ship Odds' README will be changed to match.
