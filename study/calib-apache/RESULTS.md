# Calibration hindcast on Apache Jira (2024-11-01 to 2026-11-01)

Projects kept (>= 200 Fixed issues): 25

| variant | horizon | level | projects | mean stated | mean hit | gap | share below |
|---|---|---|---|---|---|---|---|
| A (iid, W=90) | 14 | 0.5 | 25 | 0.5424 | 0.5342 | 0.0082 | 0.48 |
| A (iid, W=90) | 14 | 0.7 | 25 | 0.7432 | 0.6766 | 0.0666 | 0.84 |
| A (iid, W=90) | 14 | 0.85 | 25 | 0.8824 | 0.7998 | 0.0827 | 0.92 |
| A (iid, W=90) | 14 | 0.95 | 25 | 0.966 | 0.9047 | 0.0613 | 0.96 |
| A (iid, W=90) | 28 | 0.5 | 25 | 0.529 | 0.5373 | -0.0083 | 0.4 |
| A (iid, W=90) | 28 | 0.7 | 25 | 0.7264 | 0.6493 | 0.0771 | 0.76 |
| A (iid, W=90) | 28 | 0.85 | 25 | 0.8692 | 0.7509 | 0.1183 | 0.96 |
| A (iid, W=90) | 28 | 0.95 | 25 | 0.9597 | 0.851 | 0.1087 | 1.0 |
| B (iid, W=30) | 14 | 0.5 | 25 | 0.5509 | 0.5495 | 0.0014 | 0.48 |
| B (iid, W=30) | 14 | 0.7 | 25 | 0.7481 | 0.6941 | 0.0539 | 0.8 |
| B (iid, W=30) | 14 | 0.85 | 25 | 0.8837 | 0.8125 | 0.0711 | 0.92 |
| B (iid, W=30) | 14 | 0.95 | 25 | 0.9659 | 0.9028 | 0.0632 | 1.0 |
| B (iid, W=30) | 28 | 0.5 | 25 | 0.5329 | 0.5561 | -0.0232 | 0.36 |
| B (iid, W=30) | 28 | 0.7 | 25 | 0.7333 | 0.6695 | 0.0638 | 0.92 |
| B (iid, W=30) | 28 | 0.85 | 25 | 0.8717 | 0.76 | 0.1117 | 1.0 |
| B (iid, W=30) | 28 | 0.95 | 25 | 0.9608 | 0.8482 | 0.1126 | 1.0 |
| C (iid, W=180) | 14 | 0.5 | 25 | 0.5429 | 0.5489 | -0.006 | 0.44 |
| C (iid, W=180) | 14 | 0.7 | 25 | 0.7425 | 0.6866 | 0.0559 | 0.6 |
| C (iid, W=180) | 14 | 0.85 | 25 | 0.8811 | 0.7894 | 0.0916 | 0.8 |
| C (iid, W=180) | 14 | 0.95 | 25 | 0.9659 | 0.89 | 0.0759 | 0.84 |
| C (iid, W=180) | 28 | 0.5 | 25 | 0.5278 | 0.5323 | -0.0045 | 0.44 |
| C (iid, W=180) | 28 | 0.7 | 25 | 0.7265 | 0.6511 | 0.0754 | 0.68 |
| C (iid, W=180) | 28 | 0.85 | 25 | 0.8699 | 0.7486 | 0.1212 | 0.8 |
| C (iid, W=180) | 28 | 0.95 | 25 | 0.9596 | 0.8365 | 0.123 | 1.0 |
| D (block, W=91) | 14 | 0.5 | 25 | 0.5457 | 0.5446 | 0.0011 | 0.4 |
| D (block, W=91) | 14 | 0.7 | 25 | 0.7485 | 0.7042 | 0.0442 | 0.76 |
| D (block, W=91) | 14 | 0.85 | 25 | 0.886 | 0.827 | 0.059 | 0.92 |
| D (block, W=91) | 14 | 0.95 | 25 | 0.9674 | 0.9173 | 0.0501 | 0.92 |
| D (block, W=91) | 28 | 0.5 | 25 | 0.5285 | 0.5438 | -0.0153 | 0.4 |
| D (block, W=91) | 28 | 0.7 | 25 | 0.7285 | 0.6651 | 0.0635 | 0.72 |
| D (block, W=91) | 28 | 0.85 | 25 | 0.8706 | 0.7696 | 0.101 | 0.96 |
| D (block, W=91) | 28 | 0.95 | 25 | 0.9605 | 0.8674 | 0.0932 | 1.0 |

## Synthetic iid control (should be near calibrated)

```
{
 "A_h14": {
  "0.5": {
   "projects": 10,
   "mean_hit": 0.5211,
   "mean_stated": 0.5486,
   "gap_stated_minus_hit": 0.0275,
   "median_hit": 0.5278,
   "share_below_stated": 0.8
  },
  "0.7": {
   "projects": 10,
   "mean_hit": 0.7267,
   "mean_stated": 0.7414,
   "gap_stated_minus_hit": 0.0148,
   "median_hit": 0.7278,
   "share_below_stated": 0.5
  },
  "0.85": {
   "projects": 10,
   "mean_hit": 0.8489,
   "mean_stated": 0.8779,
   "gap_stated_minus_hit": 0.029,
   "median_hit": 0.8444,
   "share_below_stated": 0.8
  },
  "0.95": {
   "projects": 10,
   "mean_hit": 0.9456,
   "mean_stated": 0.9621,
   "gap_stated_minus_hit": 0.0165,
   "median_hit": 0.9389,
   "share_below_stated": 0.8
  }
 },
 "A_h28": {
  "0.5": {
   "projects": 10,
   "mean_hit": 0.4977,
   "mean_stated": 0.535,
   "gap_stated_minus_hit": 0.0373,
   "median_hit": 0.5,
   "share_below_stated": 0.9
  },
  "0.7": {
   "projects": 10,
   "mean_hit": 0.6761,
   "mean_stated": 0.7295,
   "gap_stated_minus_hit": 0.0534,
   "median_hit": 0.6875,
   "share_below_stated": 1.0
  },
  "0.85": {
   "projects": 10,
   "mean_hit": 0.8295,
   "mean_stated": 0.8691,
   "gap_stated_minus_hit": 0.0395,
   "median_hit": 0.8352,
   "share_below_stated": 0.9
  },
  "0.95": {
   "projects": 10,
   "mean_hit": 0.9239,
   "mean_stated": 0.9587,
   "gap_stated_minus_hit": 0.0348,
   "median_hit": 0.9261,
   "share_below_stated": 0.8
  }
 }
}
```

## Pre-registered predictions

```
{
 "P1_A_h14_085_mean_hit_below_0.80": {
  "value": 0.7998,
  "held": true
 },
 "P2_A_h14_095_mean_hit_below_0.90": {
  "value": 0.9047,
  "held": false
 },
 "P3_D_gap_smaller_than_A_gap": {
  "A": 0.0827,
  "D": 0.059,
  "held": true
 },
 "P4_A_gap_larger_at_h28": {
  "h14": 0.0827,
  "h28": 0.1183,
  "held": true
 },
 "P5_B_gap_larger_than_A": {
  "A": 0.0827,
  "B": 0.0711,
  "held": false
 },
 "P6_half_projects_below_stated": {
  "share": 0.92,
  "held": true
 }
}
```
