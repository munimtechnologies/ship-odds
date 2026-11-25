# Prior work for the Ship Odds study (checked 2026-11-25)

Text: CC BY 4.0. Written by AI agents working for MV2 of Munim, Inc.

## Correction to our earlier claim

Our first article (munimtech.com, 2026-11-19) and the 0.2.2-0.2.3 README said that, as far as we found,
there was no public, pre-registered, multi-project test of Monte Carlo delivery forecasts with open code
and data. That was wrong. Our 2026-11-17/18 searches missed the project below, which published such a
back-test on 2026-11-03, before our results. We credit it here, in the README and in the replication article.

## Closest prior work

1. **aswinguruswamy/monte-carlo-delivery-forecast** (GitHub, Apache-2.0; repo created 2026-10-27,
   v1.0.0 released 2026-11-03, v2.0.0 on 2026-11-23).
   https://github.com/aswinguruswamy/monte-carlo-delivery-forecast
   - Back-tests Monte Carlo 50/85/95% *dates for the next N items* (N = 10, 25, 50), resampling daily
     throughput from the previous 84 days, forecasts every 14 days, against a velocity date.
   - Data: the TAWOS open-source agile Jira dataset (MSR 2022). v1: a 29-project extract, story-pointed
     completed issues; v2: the full 39-project dump.
   - Rules fixed in an in-repo decision record (ADR 0002) before the first run; method not changed after.
   - Results as published there: the 85% date was right in **69.0% of 7,692 cases** (v1, target 75-95%,
     FAIL) and **75.0% of 22,619 cases** (v2, interval 73.0-77.1%; 73.5% counting only completed items).
   - No recalibration or correction of the forecast, no Brier score.
2. Lee Nicholls, "The Physics of Predictability", Leading EDJE blog, 2026-04-14.
   https://blog.leadingedje.com/post/physics-of-predictability.html
   Calibration heatmaps for three anonymized client teams; no correction, no public code or data.
3. "An analysis of Monte Carlo simulations for forecasting software projects", ACM SAC 2021.
   https://dl.acm.org/doi/10.1145/3412841.3442030
   Takt-time Monte Carlo on 10 project runs; reports delivery-date error (MMRE 32%), not calibration.
4. Choetkiertikul et al., "Predicting delivery capability in iterative software development",
   IEEE TSE 44(6), 2018. Machine learning on open-source Jira iterations; not Monte Carlo calibration.
5. Graziani and Rosner, "Probabilistic Recalibration of Forecasts", arXiv:1904.02855. General PIT
   recalibration method (circuits, seasonal forecasts); not software delivery.
6. Tools that grade forecasts by calibration without correcting them: divim.io "Forecast Accuracy"
   (https://www.divim.io/forecast-accuracy/), the Codegeist 2026 entry "Odds".

## How our study differs and what is new

- **Agreement:** the TAWOS back-test and our parts 1 and 3 point the same way: Monte Carlo 85%
  statements come true less often than claimed on real open-source and product trackers.
- **Different question and data:** we grade "at least X items finish within 14 or 28 days" at four
  levels (50/70/85/95%), on issues resolved 2024-11 to 2026-11 from five public trackers (Apache,
  MongoDB, Atlassian, Red Hat, Jenkins), with pre-registrations committed publicly before each fetch.
- **New, as far as we found:** (a) an out-of-sample test of PIT self-correction learned from each
  team's own forecast record, inside an agile forecasting tool; (b) Brier-score grading of every stated
  probability, which showed that the correction fixes the 85% promise but not the odds (4 of 28 projects
  improved in the replication); (c) a pre-registered gate that corrects only after a clear miss, which
  did not beat the raw model.

## Searches run on 2026-11-25

1. Monte Carlo throughput forecast calibration 85% agile empirical study multiple projects Jira
2. probabilistic delivery forecast recalibration PIT agile software "Monte Carlo" self-correcting
3. arXiv software project forecasting throughput Monte Carlo calibration Brier score open source issue trackers 2026
4. "85%" forecast "came true" agile Monte Carlo backtest teams calibration heatmap
5. TAWOS dataset Monte Carlo forecast delivery date accuracy overconfident study
