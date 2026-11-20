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


class Part3MatchesResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rep = load("replicate-trackers", "results.json")
        with open(os.path.join(HERE, "GRADING.md"), encoding="utf-8") as f:
            cls.grading = f.read()
        cls.per = cls.rep["per_project"]["A_h14"]
        cls.arms = cls.rep["summaries"]["A_h14"]["summary"]["arms"]

    def test_verdicts(self):
        held = {k.split("_")[0]: v["held"] for k, v in self.rep["predictions"].items()}
        self.assertEqual(held, {"T1": True, "T2": True, "T3": True, "T4": True, "T5": True, "T6": False, "T7": True})
        self.assertIn("**the gate is not adopted.**", self.grading)

    def test_kept_projects_listed(self):
        kept = self.rep["projects_kept"]
        self.assertEqual(len(kept), 28)
        self.assertEqual(sorted(self.per), sorted(kept))
        by_tracker = {}
        for key in kept:
            tracker, project = key.split(":")
            by_tracker[tracker] = by_tracker.get(tracker, 0) + 1
            self.assertIn(project, self.grading)
        self.assertEqual(by_tracker, {"mongodb": 10, "atlassian": 8, "jenkins": 1, "redhat": 9})
        self.assertEqual(len(self.rep["fetched"]), 47)

    def test_headline_numbers_quoted(self):
        for arm in ("raw", "cal", "gated", "k40"):
            self.assertIn(str(self.arms[arm]["brier"]), self.grading, arm)
        for arm in ("raw", "cal"):
            self.assertIn(str(self.arms[arm]["levels"]["0.85"]["hit"]), self.grading, arm)
        self.assertEqual(self.arms["raw"]["levels"]["0.85"]["hit"], 0.8363)
        self.assertEqual(self.arms["cal"]["levels"]["0.85"]["hit"], 0.8664)

    def test_cal_better_projects(self):
        better = sorted(k for k, r in self.per.items() if r["arms"]["cal"]["brier"] < r["arms"]["raw"]["brier"])
        self.assertEqual(better, ["atlassian:CONFSERVER", "mongodb:CDRIVER", "mongodb:NODE", "mongodb:PYTHON"])
        self.assertAlmostEqual(len(better) / 28, self.arms["cal"]["share_better_than_raw"], places=4)

    def test_gate_counts(self):
        closed = [k for k, r in self.per.items() if r["gate_share"] == 0]
        opened = [k for k, r in self.per.items() if r["gate_share"] > 0]
        self.assertEqual((len(closed), len(opened)), (17, 11))
        for k in closed:  # a gate that never opens must return the raw forecast exactly
            self.assertEqual(self.per[k]["arms"]["gated"]["brier"], self.per[k]["arms"]["raw"]["brier"], k)
        better = [k for k in opened if self.per[k]["arms"]["gated"]["brier"] < self.per[k]["arms"]["raw"]["brier"]]
        self.assertEqual(better, ["mongodb:PYTHON"])
        wfly = self.per["redhat:WFLY"]
        self.assertAlmostEqual(wfly["gate_share"], 0.78, places=2)
        self.assertEqual(round(wfly["arms"]["raw"]["brier"], 5), 0.19533)
        self.assertEqual(round(wfly["arms"]["gated"]["brier"], 5), 0.21572)
        self.assertIn("0.19533 to 0.21572", self.grading)


if __name__ == "__main__":
    unittest.main()
