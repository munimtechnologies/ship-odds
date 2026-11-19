# Part 2: PIT recalibration, prequential, Apache Jira (2024-11-01 to 2026-11-01)

Projects kept: 25. Projects per run need >= 20 evaluated origins.

| run | level | projects | raw stated | raw hit | raw gap | corrected stated | corrected hit | corrected gap | sharpness |
|---|---|---|---|---|---|---|---|---|---|
| A_h14 | 0.5 | 25 | 0.5424 | 0.5339 | 0.0085 | 0.5469 | 0.5445 | 0.0025 | 0.996 |
| A_h14 | 0.7 | 25 | 0.7428 | 0.6764 | 0.0664 | 0.75 | 0.7137 | 0.0363 | 0.9252 |
| A_h14 | 0.85 | 25 | 0.8823 | 0.7934 | 0.089 | 0.8908 | 0.8465 | 0.0443 | 0.8619 |
| A_h14 | 0.95 | 25 | 0.9655 | 0.8972 | 0.0683 | 0.9742 | 0.9314 | 0.0428 | 0.7941 |
| A_h14 | Brier | 25 | | | 0.18223 | | | 0.18075 | better in 0.32 |
| A_h28 | 0.5 | 25 | 0.5284 | 0.5288 | 0.0004 | 0.535 | 0.5286 | 0.0064 | 1.0178 |
| A_h28 | 0.7 | 25 | 0.7261 | 0.6417 | 0.0845 | 0.7333 | 0.6719 | 0.0614 | 0.9334 |
| A_h28 | 0.85 | 25 | 0.8694 | 0.74 | 0.1294 | 0.8781 | 0.8122 | 0.0659 | 0.8626 |
| A_h28 | 0.95 | 25 | 0.9598 | 0.8402 | 0.1196 | 0.9741 | 0.913 | 0.0611 | 0.7349 |
| A_h28 | Brier | 25 | | | 0.20935 | | | 0.21024 | better in 0.2 |
| D_h14 | 0.5 | 25 | 0.5473 | 0.5521 | 0.0048 | 0.5531 | 0.5512 | 0.0018 | 1.0231 |
| D_h14 | 0.7 | 25 | 0.7483 | 0.6959 | 0.0524 | 0.7553 | 0.7228 | 0.0326 | 0.946 |
| D_h14 | 0.85 | 25 | 0.8855 | 0.817 | 0.0685 | 0.8949 | 0.8567 | 0.0381 | 0.878 |
| D_h14 | 0.95 | 25 | 0.9677 | 0.9048 | 0.0629 | 0.9745 | 0.9347 | 0.0398 | 0.8071 |
| D_h14 | Brier | 25 | | | 0.17249 | | | 0.17398 | better in 0.2 |

## Controls

```
{
 "iid": {
  "projects": 8,
  "levels": {
   "0.5": {
    "projects": 8,
    "raw_stated": 0.5522,
    "raw_hit": 0.5503,
    "raw_gap": 0.0019,
    "cal_stated": 0.555,
    "cal_hit": 0.5698,
    "cal_gap": 0.0148,
    "sharpness": 0.9837
   },
   "0.7": {
    "projects": 8,
    "raw_stated": 0.7436,
    "raw_hit": 0.7614,
    "raw_gap": 0.0178,
    "cal_stated": 0.7582,
    "cal_hit": 0.7727,
    "cal_gap": 0.0146,
    "sharpness": 0.98
   },
   "0.85": {
    "projects": 8,
    "raw_stated": 0.8793,
    "raw_hit": 0.8685,
    "raw_gap": 0.0108,
    "cal_stated": 0.884,
    "cal_hit": 0.8864,
    "cal_gap": 0.0024,
    "sharpness": 0.9628
   },
   "0.95": {
    "projects": 8,
    "raw_stated": 0.9634,
    "raw_hit": 0.9529,
    "raw_gap": 0.0104,
    "cal_stated": 0.9724,
    "cal_hit": 0.9513,
    "cal_gap": 0.0211,
    "sharpness": 0.8918
   }
  },
  "brier_raw": 0.14668,
  "brier_cal": 0.15336,
  "share_projects_cal_better": 0.0
 },
 "drift_down": {
  "projects": 8,
  "levels": {
   "0.5": {
    "projects": 8,
    "raw_stated": 0.5362,
    "raw_hit": 0.3068,
    "raw_gap": 0.2293,
    "cal_stated": 0.5414,
    "cal_hit": 0.4513,
    "cal_gap": 0.0901,
    "sharpness": 0.9317
   },
   "0.7": {
    "projects": 8,
    "raw_stated": 0.7295,
    "raw_hit": 0.474,
    "raw_gap": 0.2555,
    "cal_stated": 0.7348,
    "cal_hit": 0.6396,
    "cal_gap": 0.0952,
    "sharpness": 0.9174
   },
   "0.85": {
    "projects": 8,
    "raw_stated": 0.8705,
    "raw_hit": 0.6688,
    "raw_gap": 0.2017,
    "cal_stated": 0.8765,
    "cal_hit": 0.8149,
    "cal_gap": 0.0616,
    "sharpness": 0.8892
   },
   "0.95": {
    "projects": 8,
    "raw_stated": 0.959,
    "raw_hit": 0.8393,
    "raw_gap": 0.1197,
    "cal_stated": 0.9714,
    "cal_hit": 0.9351,
    "cal_gap": 0.0364,
    "sharpness": 0.8506
   }
  },
  "brier_raw": 0.24732,
  "brier_cal": 0.21735,
  "share_projects_cal_better": 1.0
 }
}
```

## Pre-registered predictions

```
{
 "R1_h14_085_cal_gap_smaller": {
  "raw_gap": 0.089,
  "cal_gap": 0.0443,
  "held": true
 },
 "R2_h14_085_cal_hit_in_0.80_0.90": {
  "cal_hit": 0.8465,
  "held": true
 },
 "R3_h14_brier_lower": {
  "raw": 0.18223,
  "cal": 0.18075,
  "held": true
 },
 "R4_h28_085_cal_gap_smaller": {
  "raw_gap": 0.1294,
  "cal_gap": 0.0659,
  "held": true
 },
 "R5_h14_share_projects_better_ge_0.6": {
  "share": 0.32,
  "held": false
 }
}
```
