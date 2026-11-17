# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Offline tests for the part 2 recalibration study (no network)."""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recal  # noqa: E402


class PitAndMap(unittest.TestCase):
    def test_pit(self):
        t = [1, 2, 2, 3]
        self.assertEqual(recal.pit(t, 2, 0.0), 0.25)
        self.assertEqual(recal.pit(t, 2, 1.0), 0.75)
        self.assertEqual(recal.pit(t, 0, 0.5), 0.0)
        self.assertEqual(recal.pit(t, 9, 0.5), 1.0)

    def test_identity_map_changes_nothing(self):
        g = recal.make_g([])
        # 499 draws, so no level times n is a whole number (no exact ties at a level).
        t = sorted(random.Random(1).choices(range(20), k=499))
        for x in (1, 5, 10, 15, 25):
            self.assertAlmostEqual(recal.corrected_ge(t, x, g), recal.raw_ge(t, x))
        for L in recal.LEVELS:
            y = recal.corrected_level_x(t, L, g)
            self.assertGreaterEqual(recal.corrected_ge(t, y, g), L)
            self.assertLess(recal.corrected_ge(t, y + 1, g), L)
            self.assertGreaterEqual(y, recal.quantile(t, 1 - L))

    def test_slow_history_lowers_the_count(self):
        t = sorted(random.Random(2).choices(range(20), k=500))
        g = recal.make_g([0.02] * 40)
        for L in (0.7, 0.85):
            self.assertLess(recal.corrected_level_x(t, L, g), recal.quantile(t, 1 - L))
        self.assertEqual(recal.corrected_ge(t, 0, g), 1.0)

    def test_matches_ship_odds_js_formula(self):
        # JS: correctProbability(p, G) = 1 - G(1 - p) with p = P(T >= x) = 1 - F(x - 1).
        t = sorted(random.Random(3).choices(range(30), k=401))  # 401: c/n never equals a PIT below
        g = recal.make_g([0.1, 0.2, 0.05, 0.4, 0.9] * 4)
        for x in (3, 10, 17, 26):
            p = recal.raw_ge(t, x)
            self.assertAlmostEqual(recal.corrected_ge(t, x, g), 1 - g(1 - p))


class Prequential(unittest.TestCase):
    def test_iid_team_stays_near_calibrated(self):
        rng = random.Random(5)
        counts = [recal.poisson(rng, 2.0) for _ in range(500)]
        r = recal.prequential(counts, 90, 14, runs=400)
        self.assertGreaterEqual(r["evaluated"], 20)
        row = r["table"][recal.LEVELS.index(0.85)]
        self.assertGreater(row["raw_hit"], 0.65)
        self.assertGreater(row["cal_hit"], 0.65)
        self.assertLess(abs(r["brier_cal"] - r["brier_raw"]), 0.05)

    def test_drifting_team_gets_corrected(self):
        rng = random.Random(6)
        counts = [recal.poisson(rng, max(0.3, 5.0 * (1 - d / 650))) for d in range(600)]
        r = recal.prequential(counts, 90, 14, runs=400)
        row = r["table"][recal.LEVELS.index(0.85)]
        self.assertLess(row["raw_hit"], 0.75, row)
        self.assertGreater(row["cal_hit"], row["raw_hit"] + 0.05, row)
        self.assertLess(r["brier_cal"], r["brier_raw"])
        self.assertLess(r["mean_pit"], 0.45)

    def test_no_peeking(self):
        # 200 days, window 90, h 14: origins 95, 102, ..., 186 (14 of them). An origin may only use
        # PITs whose 14-day horizon had ended (t_j + 14 <= t). Origin 179 sees 11 such PITs (too few);
        # only origin 186 sees 12. Using unfinished horizons would let 179 (and 172) through.
        counts = [2] * 200
        r = recal.prequential(counts, 90, 14, step=7, runs=50)
        self.assertEqual(r["evaluated"], 1)

    def test_summarize(self):
        rng = random.Random(7)
        res = {f"P{i}": recal.prequential([recal.poisson(rng, 1.5) for _ in range(400)], 90, 14, runs=200)
               for i in range(3)}
        s = recal.summarize(res)
        self.assertEqual(s["projects"], 3)
        self.assertIn("0.85", s["levels"])
        self.assertIn("brier_cal", s)
        self.assertTrue(0 <= s["share_projects_cal_better"] <= 1)


if __name__ == "__main__":
    unittest.main()
