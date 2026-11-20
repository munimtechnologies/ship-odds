# Part 3: replication on four public Jira trackers (2024-11-01 to 2026-11-01)

Projects kept: 28 (>= 200 issues; per run >= 20 evaluated origins).

### A_h14 (28 projects)

| arm | level | stated | hit | gap | share below | sharpness |
|---|---|---|---|---|---|---|
| raw | 0.5 | 0.5439 | 0.5455 | -0.0015 | 0.6071 | 1.0 |
| raw | 0.7 | 0.7486 | 0.7064 | 0.0422 | 0.7143 | 1.0 |
| raw | 0.85 | 0.8908 | 0.8363 | 0.0545 | 0.8214 | 1.0 |
| raw | 0.95 | 0.9714 | 0.9351 | 0.0364 | 0.8929 | 1.0 |
| raw | Brier | | | 0.16219 | better than raw in 0.0 | |
| cal | 0.5 | 0.5479 | 0.5547 | -0.0068 | 0.4643 | 1.0068 |
| cal | 0.7 | 0.7549 | 0.7384 | 0.0165 | 0.5 | 0.9727 |
| cal | 0.85 | 0.8977 | 0.8664 | 0.0313 | 0.8214 | 0.9273 |
| cal | 0.95 | 0.9791 | 0.9518 | 0.0274 | 0.9286 | 0.7524 |
| cal | Brier | | | 0.16691 | better than raw in 0.1429 | |
| gated | 0.5 | 0.5443 | 0.5445 | -0.0002 | 0.6786 | 0.9994 |
| gated | 0.7 | 0.7506 | 0.7175 | 0.0331 | 0.6786 | 0.9872 |
| gated | 0.85 | 0.8925 | 0.8409 | 0.0516 | 0.8214 | 0.9809 |
| gated | 0.95 | 0.9724 | 0.9378 | 0.0346 | 0.8929 | 0.9731 |
| gated | Brier | | | 0.16365 | better than raw in 0.0357 | |
| k40 | 0.5 | 0.545 | 0.5492 | -0.0042 | 0.5 | 1.0042 |
| k40 | 0.7 | 0.7502 | 0.725 | 0.0253 | 0.6429 | 0.9795 |
| k40 | 0.85 | 0.8933 | 0.859 | 0.0343 | 0.8214 | 0.9386 |
| k40 | 0.95 | 0.9747 | 0.9499 | 0.0248 | 0.8571 | 0.814 |
| k40 | Brier | | | 0.16369 | better than raw in 0.25 | |

Mean share of forecasts where the gate was open: 0.096

### A_h28 (28 projects)

| arm | level | stated | hit | gap | share below | sharpness |
|---|---|---|---|---|---|---|
| raw | 0.5 | 0.529 | 0.5308 | -0.0018 | 0.5357 | 1.0 |
| raw | 0.7 | 0.7273 | 0.6815 | 0.0458 | 0.75 | 1.0 |
| raw | 0.85 | 0.8712 | 0.8014 | 0.0698 | 0.7857 | 1.0 |
| raw | 0.95 | 0.9618 | 0.8938 | 0.0679 | 0.9286 | 1.0 |
| raw | Brier | | | 0.18142 | better than raw in 0.0 | |
| cal | 0.5 | 0.5319 | 0.5411 | -0.0092 | 0.5 | 1.0051 |
| cal | 0.7 | 0.7363 | 0.7275 | 0.0088 | 0.6429 | 0.9467 |
| cal | 0.85 | 0.8816 | 0.8469 | 0.0347 | 0.6786 | 0.9004 |
| cal | 0.95 | 0.9735 | 0.931 | 0.0425 | 0.9286 | 0.8428 |
| cal | Brier | | | 0.19112 | better than raw in 0.1429 | |
| gated | 0.5 | 0.5284 | 0.5431 | -0.0147 | 0.5357 | 1.0094 |
| gated | 0.7 | 0.7302 | 0.7089 | 0.0213 | 0.6429 | 0.9648 |
| gated | 0.85 | 0.8755 | 0.8366 | 0.0389 | 0.75 | 0.931 |
| gated | 0.95 | 0.9677 | 0.9198 | 0.0479 | 0.8929 | 0.8975 |
| gated | Brier | | | 0.18743 | better than raw in 0.1071 | |
| k40 | 0.5 | 0.5269 | 0.5338 | -0.0068 | 0.5 | 1.0044 |
| k40 | 0.7 | 0.7299 | 0.7065 | 0.0235 | 0.6429 | 0.9688 |
| k40 | 0.85 | 0.8738 | 0.8366 | 0.0372 | 0.7143 | 0.9322 |
| k40 | 0.95 | 0.965 | 0.9247 | 0.0403 | 0.8929 | 0.8775 |
| k40 | Brier | | | 0.18424 | better than raw in 0.2143 | |

Mean share of forecasts where the gate was open: 0.3165

### A_h14, tracker mongodb (10 projects)

| arm | level | stated | hit | gap | share below | sharpness |
|---|---|---|---|---|---|---|
| raw | 0.5 | 0.5603 | 0.526 | 0.0343 | 0.8 | 1.0 |
| raw | 0.7 | 0.7597 | 0.6753 | 0.0844 | 0.9 | 1.0 |
| raw | 0.85 | 0.8927 | 0.8065 | 0.0862 | 1.0 | 1.0 |
| raw | 0.95 | 0.9725 | 0.9169 | 0.0556 | 0.9 | 1.0 |
| raw | Brier | | | 0.17629 | better than raw in 0.0 | |
| cal | 0.5 | 0.5572 | 0.5584 | -0.0013 | 0.5 | 0.9704 |
| cal | 0.7 | 0.7631 | 0.7377 | 0.0254 | 0.7 | 0.8867 |
| cal | 0.85 | 0.9056 | 0.8571 | 0.0485 | 0.9 | 0.7467 |
| cal | 0.95 | 0.983 | 0.9519 | 0.031 | 0.9 | 0.6253 |
| cal | Brier | | | 0.17994 | better than raw in 0.3 | |
| gated | 0.5 | 0.5616 | 0.5299 | 0.0317 | 0.9 | 0.9945 |
| gated | 0.7 | 0.7648 | 0.7 | 0.0648 | 0.9 | 0.9752 |
| gated | 0.85 | 0.8959 | 0.813 | 0.083 | 1.0 | 0.9655 |
| gated | 0.95 | 0.9743 | 0.9208 | 0.0535 | 0.9 | 0.9535 |
| gated | Brier | | | 0.17636 | better than raw in 0.1 | |
| k40 | 0.5 | 0.5562 | 0.5455 | 0.0107 | 0.6 | 0.9818 |
| k40 | 0.7 | 0.7602 | 0.7078 | 0.0524 | 0.9 | 0.9324 |
| k40 | 0.85 | 0.8999 | 0.8468 | 0.0531 | 1.0 | 0.8219 |
| k40 | 0.95 | 0.9768 | 0.9455 | 0.0314 | 0.7 | 0.7363 |
| k40 | Brier | | | 0.17701 | better than raw in 0.4 | |

Mean share of forecasts where the gate was open: 0.1143

### A_h14, tracker atlassian (8 projects)

| arm | level | stated | hit | gap | share below | sharpness |
|---|---|---|---|---|---|---|
| raw | 0.5 | 0.5342 | 0.539 | -0.0047 | 0.625 | 1.0 |
| raw | 0.7 | 0.7428 | 0.7078 | 0.035 | 0.625 | 1.0 |
| raw | 0.85 | 0.8976 | 0.8523 | 0.0454 | 0.75 | 1.0 |
| raw | 0.95 | 0.9764 | 0.9545 | 0.0219 | 0.875 | 1.0 |
| raw | Brier | | | 0.15357 | better than raw in 0.0 | |
| cal | 0.5 | 0.54 | 0.5373 | 0.0027 | 0.375 | 1.0657 |
| cal | 0.7 | 0.7501 | 0.7273 | 0.0228 | 0.5 | 1.0724 |
| cal | 0.85 | 0.8978 | 0.8653 | 0.0325 | 1.0 | 1.1464 |
| cal | 0.95 | 0.982 | 0.9594 | 0.0226 | 0.875 | 0.7923 |
| cal | Brier | | | 0.15798 | better than raw in 0.125 | |
| gated | 0.5 | 0.5344 | 0.5438 | -0.0094 | 0.625 | 0.9997 |
| gated | 0.7 | 0.7435 | 0.7045 | 0.0389 | 0.625 | 0.997 |
| gated | 0.85 | 0.8981 | 0.8539 | 0.0442 | 0.75 | 0.9982 |
| gated | 0.95 | 0.9767 | 0.9529 | 0.0238 | 0.875 | 0.9981 |
| gated | Brier | | | 0.15583 | better than raw in 0.0 | |
| k40 | 0.5 | 0.5356 | 0.539 | -0.0034 | 0.5 | 1.0389 |
| k40 | 0.7 | 0.7446 | 0.7192 | 0.0255 | 0.625 | 1.0307 |
| k40 | 0.85 | 0.8943 | 0.8636 | 0.0306 | 0.75 | 1.0749 |
| k40 | 0.95 | 0.9795 | 0.9627 | 0.0168 | 0.875 | 0.8233 |
| k40 | Brier | | | 0.15513 | better than raw in 0.25 | |

Mean share of forecasts where the gate was open: 0.0471

### A_h14, tracker jenkins (1 projects)

| arm | level | stated | hit | gap | share below | sharpness |
|---|---|---|---|---|---|---|
| raw | 0.5 | 0.5666 | 0.5455 | 0.0211 | 1.0 | 1.0 |
| raw | 0.7 | 0.7641 | 0.7143 | 0.0498 | 1.0 | 1.0 |
| raw | 0.85 | 0.9012 | 0.8701 | 0.031 | 1.0 | 1.0 |
| raw | 0.95 | 0.983 | 1.0 | -0.017 | 0.0 | 1.0 |
| raw | Brier | | | 0.14419 | better than raw in 0.0 | |
| cal | 0.5 | 0.5957 | 0.7013 | -0.1056 | 0.0 | 0.8223 |
| cal | 0.7 | 0.786 | 0.8312 | -0.0452 | 0.0 | 0.8103 |
| cal | 0.85 | 0.9238 | 0.9351 | -0.0113 | 0.0 | 0.8065 |
| cal | 0.95 | 0.9899 | 0.974 | 0.0159 | 1.0 | 0.7386 |
| cal | Brier | | | 0.1457 | better than raw in 0.0 | |
| gated | 0.5 | 0.5666 | 0.5455 | 0.0211 | 1.0 | 1.0 |
| gated | 0.7 | 0.7641 | 0.7143 | 0.0498 | 1.0 | 1.0 |
| gated | 0.85 | 0.9012 | 0.8701 | 0.031 | 1.0 | 1.0 |
| gated | 0.95 | 0.983 | 1.0 | -0.017 | 0.0 | 1.0 |
| gated | Brier | | | 0.14419 | better than raw in 0.0 | |
| k40 | 0.5 | 0.5834 | 0.6364 | -0.053 | 0.0 | 0.8934 |
| k40 | 0.7 | 0.7808 | 0.8312 | -0.0504 | 0.0 | 0.8759 |
| k40 | 0.85 | 0.916 | 0.9221 | -0.0061 | 0.0 | 0.8548 |
| k40 | 0.95 | 0.9843 | 0.974 | 0.0103 | 1.0 | 0.8864 |
| k40 | Brier | | | 0.1427 | better than raw in 1.0 | |

Mean share of forecasts where the gate was open: 0.0

### A_h14, tracker redhat (9 projects)

| arm | level | stated | hit | gap | share below | sharpness |
|---|---|---|---|---|---|---|
| raw | 0.5 | 0.5319 | 0.5729 | -0.041 | 0.3333 | 1.0 |
| raw | 0.7 | 0.7396 | 0.7388 | 0.0007 | 0.5556 | 1.0 |
| raw | 0.85 | 0.8815 | 0.8514 | 0.0301 | 0.6667 | 1.0 |
| raw | 0.95 | 0.9645 | 0.9307 | 0.0337 | 1.0 | 1.0 |
| raw | Brier | | | 0.15618 | better than raw in 0.0 | |
| cal | 0.5 | 0.5393 | 0.5498 | -0.0105 | 0.5556 | 1.0154 |
| cal | 0.7 | 0.7468 | 0.7388 | 0.008 | 0.3333 | 0.9978 |
| cal | 0.85 | 0.886 | 0.8701 | 0.0158 | 0.6667 | 0.9467 |
| cal | 0.95 | 0.9711 | 0.9423 | 0.0288 | 1.0 | 0.8501 |
| cal | Brier | | | 0.16274 | better than raw in 0.0 | |
| gated | 0.5 | 0.5316 | 0.5613 | -0.0298 | 0.4444 | 1.0047 |
| gated | 0.7 | 0.7398 | 0.7489 | -0.0092 | 0.4444 | 0.9902 |
| gated | 0.85 | 0.8828 | 0.8571 | 0.0257 | 0.6667 | 0.9805 |
| gated | 0.95 | 0.9654 | 0.9365 | 0.0289 | 1.0 | 0.9703 |
| gated | Brier | | | 0.15863 | better than raw in 0.0 | |
| k40 | 0.5 | 0.5366 | 0.5527 | -0.0161 | 0.4444 | 1.0105 |
| k40 | 0.7 | 0.7408 | 0.7374 | 0.0034 | 0.4444 | 0.9978 |
| k40 | 0.85 | 0.8826 | 0.8615 | 0.0212 | 0.7778 | 0.9565 |
| k40 | 0.95 | 0.967 | 0.9408 | 0.0262 | 1.0 | 0.8764 |
| k40 | Brier | | | 0.15885 | better than raw in 0.0 | |

Mean share of forecasts where the gate was open: 0.1299

### Exploratory: A_h14 on part 2's Apache data (25 projects)

| arm | level | stated | hit | gap | share below | sharpness |
|---|---|---|---|---|---|---|
| raw | 0.5 | 0.5424 | 0.5339 | 0.0085 | 0.48 | 1.0 |
| raw | 0.7 | 0.7428 | 0.6764 | 0.0664 | 0.8 | 1.0 |
| raw | 0.85 | 0.8823 | 0.7934 | 0.089 | 0.96 | 1.0 |
| raw | 0.95 | 0.9655 | 0.8972 | 0.0683 | 0.96 | 1.0 |
| raw | Brier | | | 0.18223 | better than raw in 0.0 | |
| cal | 0.5 | 0.5469 | 0.5445 | 0.0025 | 0.36 | 0.996 |
| cal | 0.7 | 0.75 | 0.7137 | 0.0363 | 0.64 | 0.9252 |
| cal | 0.85 | 0.8908 | 0.8465 | 0.0443 | 0.88 | 0.8619 |
| cal | 0.95 | 0.9742 | 0.9314 | 0.0428 | 0.96 | 0.7941 |
| cal | Brier | | | 0.18075 | better than raw in 0.32 | |
| gated | 0.5 | 0.5453 | 0.5414 | 0.0039 | 0.44 | 0.9933 |
| gated | 0.7 | 0.7481 | 0.6975 | 0.0506 | 0.76 | 0.9659 |
| gated | 0.85 | 0.8856 | 0.8162 | 0.0694 | 0.96 | 0.9545 |
| gated | 0.95 | 0.9678 | 0.9164 | 0.0514 | 0.92 | 0.928 |
| gated | Brier | | | 0.17977 | better than raw in 0.28 | |
| k40 | 0.5 | 0.5402 | 0.5359 | 0.0043 | 0.4 | 0.9991 |
| k40 | 0.7 | 0.7436 | 0.6976 | 0.046 | 0.64 | 0.9526 |
| k40 | 0.85 | 0.8855 | 0.8263 | 0.0592 | 0.88 | 0.903 |
| k40 | 0.95 | 0.9685 | 0.9253 | 0.0432 | 0.92 | 0.8452 |
| k40 | Brier | | | 0.1795 | better than raw in 0.32 | |

Mean share of forecasts where the gate was open: 0.1901

## Controls

```
{
 "iid": {
  "projects": 8,
  "arms": {
   "raw": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.5522,
      "hit": 0.5503,
      "gap": 0.0019,
      "abs_gap": 0.0019,
      "share_below": 0.375,
      "sharpness": 1.0
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7436,
      "hit": 0.7614,
      "gap": -0.0178,
      "abs_gap": 0.0178,
      "share_below": 0.125,
      "sharpness": 1.0
     },
     "0.85": {
      "projects": 8,
      "stated": 0.8793,
      "hit": 0.8685,
      "gap": 0.0108,
      "abs_gap": 0.0108,
      "share_below": 0.625,
      "sharpness": 1.0
     },
     "0.95": {
      "projects": 8,
      "stated": 0.9634,
      "hit": 0.9529,
      "gap": 0.0104,
      "abs_gap": 0.0104,
      "share_below": 0.75,
      "sharpness": 1.0
     }
    },
    "brier": 0.14668,
    "share_better_than_raw": 0.0
   },
   "cal": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.555,
      "hit": 0.5698,
      "gap": -0.0148,
      "abs_gap": 0.0148,
      "share_below": 0.375,
      "sharpness": 0.9837
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7582,
      "hit": 0.7727,
      "gap": -0.0146,
      "abs_gap": 0.0146,
      "share_below": 0.375,
      "sharpness": 0.98
     },
     "0.85": {
      "projects": 8,
      "stated": 0.884,
      "hit": 0.8864,
      "gap": -0.0024,
      "abs_gap": 0.0024,
      "share_below": 0.375,
      "sharpness": 0.9628
     },
     "0.95": {
      "projects": 8,
      "stated": 0.9724,
      "hit": 0.9513,
      "gap": 0.0211,
      "abs_gap": 0.0211,
      "share_below": 1.0,
      "sharpness": 0.8918
     }
    },
    "brier": 0.15336,
    "share_better_than_raw": 0.0
   },
   "gated": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.5521,
      "hit": 0.5519,
      "gap": 0.0002,
      "abs_gap": 0.0002,
      "share_below": 0.375,
      "sharpness": 0.9995
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7436,
      "hit": 0.7614,
      "gap": -0.0178,
      "abs_gap": 0.0178,
      "share_below": 0.125,
      "sharpness": 0.9986
     },
     "0.85": {
      "projects": 8,
      "stated": 0.8795,
      "hit": 0.8685,
      "gap": 0.011,
      "abs_gap": 0.011,
      "share_below": 0.625,
      "sharpness": 0.9985
     },
     "0.95": {
      "projects": 8,
      "stated": 0.9634,
      "hit": 0.9529,
      "gap": 0.0105,
      "abs_gap": 0.0105,
      "share_below": 0.75,
      "sharpness": 0.9979
     }
    },
    "brier": 0.14733,
    "share_better_than_raw": 0.0
   },
   "k40": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.5511,
      "hit": 0.5617,
      "gap": -0.0106,
      "abs_gap": 0.0106,
      "share_below": 0.375,
      "sharpness": 0.9917
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7508,
      "hit": 0.7711,
      "gap": -0.0203,
      "abs_gap": 0.0203,
      "share_below": 0.25,
      "sharpness": 0.9898
     },
     "0.85": {
      "projects": 8,
      "stated": 0.88,
      "hit": 0.8831,
      "gap": -0.0031,
      "abs_gap": 0.0031,
      "share_below": 0.375,
      "sharpness": 0.9776
     },
     "0.95": {
      "projects": 8,
      "stated": 0.965,
      "hit": 0.9529,
      "gap": 0.0121,
      "abs_gap": 0.0121,
      "share_below": 0.75,
      "sharpness": 0.9375
     }
    },
    "brier": 0.14977,
    "share_better_than_raw": 0.0
   }
  },
  "mean_gate_share": 0.0114
 },
 "drift_down": {
  "projects": 8,
  "arms": {
   "raw": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.5362,
      "hit": 0.3068,
      "gap": 0.2293,
      "abs_gap": 0.2293,
      "share_below": 1.0,
      "sharpness": 1.0
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7295,
      "hit": 0.474,
      "gap": 0.2555,
      "abs_gap": 0.2555,
      "share_below": 1.0,
      "sharpness": 1.0
     },
     "0.85": {
      "projects": 8,
      "stated": 0.8705,
      "hit": 0.6688,
      "gap": 0.2017,
      "abs_gap": 0.2017,
      "share_below": 1.0,
      "sharpness": 1.0
     },
     "0.95": {
      "projects": 8,
      "stated": 0.959,
      "hit": 0.8393,
      "gap": 0.1197,
      "abs_gap": 0.1197,
      "share_below": 1.0,
      "sharpness": 1.0
     }
    },
    "brier": 0.24732,
    "share_better_than_raw": 0.0
   },
   "cal": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.5414,
      "hit": 0.4513,
      "gap": 0.0901,
      "abs_gap": 0.0901,
      "share_below": 1.0,
      "sharpness": 0.9317
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7348,
      "hit": 0.6396,
      "gap": 0.0952,
      "abs_gap": 0.0952,
      "share_below": 1.0,
      "sharpness": 0.9174
     },
     "0.85": {
      "projects": 8,
      "stated": 0.8765,
      "hit": 0.8149,
      "gap": 0.0616,
      "abs_gap": 0.0616,
      "share_below": 1.0,
      "sharpness": 0.8892
     },
     "0.95": {
      "projects": 8,
      "stated": 0.9714,
      "hit": 0.9351,
      "gap": 0.0364,
      "abs_gap": 0.0364,
      "share_below": 0.875,
      "sharpness": 0.8506
     }
    },
    "brier": 0.21735,
    "share_better_than_raw": 1.0
   },
   "gated": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.538,
      "hit": 0.4042,
      "gap": 0.1338,
      "abs_gap": 0.1338,
      "share_below": 1.0,
      "sharpness": 0.9592
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7324,
      "hit": 0.5893,
      "gap": 0.1431,
      "abs_gap": 0.1431,
      "share_below": 1.0,
      "sharpness": 0.9484
     },
     "0.85": {
      "projects": 8,
      "stated": 0.8735,
      "hit": 0.7403,
      "gap": 0.1333,
      "abs_gap": 0.1333,
      "share_below": 1.0,
      "sharpness": 0.9415
     },
     "0.95": {
      "projects": 8,
      "stated": 0.9647,
      "hit": 0.8994,
      "gap": 0.0653,
      "abs_gap": 0.0653,
      "share_below": 1.0,
      "sharpness": 0.9274
     }
    },
    "brier": 0.23223,
    "share_better_than_raw": 1.0
   },
   "k40": {
    "levels": {
     "0.5": {
      "projects": 8,
      "stated": 0.5329,
      "hit": 0.3896,
      "gap": 0.1432,
      "abs_gap": 0.1432,
      "share_below": 1.0,
      "sharpness": 0.9596
     },
     "0.7": {
      "projects": 8,
      "stated": 0.7327,
      "hit": 0.6023,
      "gap": 0.1304,
      "abs_gap": 0.1304,
      "share_below": 1.0,
      "sharpness": 0.9472
     },
     "0.85": {
      "projects": 8,
      "stated": 0.8724,
      "hit": 0.7727,
      "gap": 0.0997,
      "abs_gap": 0.0997,
      "share_below": 1.0,
      "sharpness": 0.9275
     },
     "0.95": {
      "projects": 8,
      "stated": 0.9608,
      "hit": 0.914,
      "gap": 0.0469,
      "abs_gap": 0.0469,
      "share_below": 1.0,
      "sharpness": 0.9002
     }
    },
    "brier": 0.22242,
    "share_better_than_raw": 1.0
   }
  },
  "mean_gate_share": 0.4838
 }
}
```

## Pre-registered predictions

```
{
 "T1_raw_h14_085_gap_gt_0.03": {
  "gap": 0.0545,
  "held": true
 },
 "T2_half_projects_below_stated": {
  "share": 0.8214,
  "held": true
 },
 "T3_raw_gap_larger_at_h28": {
  "h14": 0.0545,
  "h28": 0.0698,
  "held": true
 },
 "T4_cal_abs_gap_smaller_than_raw": {
  "raw": 0.0545,
  "cal": 0.0313,
  "held": true
 },
 "T5_gated_brier_lower_than_cal": {
  "gated": 0.16365,
  "cal": 0.16691,
  "held": true
 },
 "T6_gated_brier_lower_than_raw": {
  "gated": 0.16365,
  "raw": 0.16219,
  "held": false
 },
 "T7_gated_abs_gap_smaller_than_raw": {
  "raw": 0.0545,
  "gated": 0.0516,
  "held": true
 }
}
```
