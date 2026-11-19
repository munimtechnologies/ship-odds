# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Checks that study/GRADING.md agrees with the raw result files it grades.

Standard library only. Run: python -m unittest study/test_grading.py (from the repo root) or
python -m unittest test_grading (from study/).
"""
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def load(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return json.load(f)


class GradingMatchesResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calib = load("calib-apache", "results.json")
        cls.recal = load("recal-apache", "results.json")
        with open(os.path.join(HERE, "GRADING.md"), encoding="utf-8") as f:
            cls.grading = f.read()

    def test_part1_verdicts(self):
        held = {k.split("_")[0]: v["held"] for k, v in self.calib["predictions"].items()}
        self.assertEqual(held, {"P1": True, "P2": False, "P3": True, "P4": True, "P5": False, "P6": True})

    def test_part2_verdicts(self):
        held = {k.split("_")[0]: v["held"] for k, v in self.recal["predictions"].items()}
        self.assertEqual(held, {"R1": True, "R2": True, "R3": True, "R4": True, "R5": False})

    def test_kept_projects(self):
        self.assertEqual(len(self.calib["projects_kept"]), 25)
        self.assertEqual(self.calib["projects_kept"], self.recal["projects_kept"])
        for key in self.recal["projects_kept"]:
            self.assertIn(key, self.grading)

    def test_headline_numbers_quoted(self):
        p = self.calib["predictions"]
        self.assertEqual(p["P1_A_h14_085_mean_hit_below_0.80"]["value"], 0.7998)
        s = self.recal["summaries"]["A_h14"]["summary"]
        lv = s["levels"]["0.85"]
        for value in (lv["raw_hit"], lv["cal_hit"], lv["raw_gap"], lv["cal_gap"], lv["sharpness"],
                      s["brier_raw"], s["brier_cal"]):
            self.assertIn(("%.4f" % value).rstrip("0") if value < 0.1 else str(value), self.grading)

    def test_r5_share_recomputed_from_per_project(self):
        per = self.recal["per_project"]["A_h14"]
        better = sorted(k for k, r in per.items() if r["brier_cal"] < r["brier_raw"])
        self.assertEqual(len(per), 25)
        self.assertEqual(len(better), 8)
        self.assertAlmostEqual(len(better) / len(per), self.recal["summaries"]["A_h14"]["summary"]["share_projects_cal_better"])
        for key in ("HUDI", "AMQ", "ORC", "KAFKA"):
            self.assertIn(key, better)
        gains = sorted(per, key=lambda k: per[k]["brier_cal"] - per[k]["brier_raw"])
        self.assertEqual(gains[:4], ["HUDI", "AMQ", "ORC", "KAFKA"])


if __name__ == "__main__":
    unittest.main()
