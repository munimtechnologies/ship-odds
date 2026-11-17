# SPDX-License-Identifier: Apache-2.0
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calib  # noqa: E402
import job  # noqa: E402


class CalibTests(unittest.TestCase):
    def test_parse_and_days(self):
        t = calib.parse_time("2025-01-02T10:00:00.000+0000")
        self.assertEqual(calib.day_index(t), calib.iso_to_day("2025-01-02"))
        self.assertEqual(calib.daily_counts([10, 10, 12, 9], 10, 3), [2, 0, 1])

    def test_quantile_matches_js(self):
        s = [1, 2, 3, 4]
        self.assertEqual(calib.quantile(s, 0.5), 2)
        self.assertEqual(calib.quantile(s, 0.85), 4)
        self.assertEqual(calib.quantile(s, 0.01), 1)

    def test_constant_pace_always_hits(self):
        hc = calib.hindcast([2] * 300, 90, 14, runs=200)
        self.assertGreater(hc["origins"], 20)
        for row in hc["table"]:
            self.assertEqual(row["hit_rate"], 1.0)
            self.assertEqual(row["stated"], 1.0)

    def test_falling_pace_is_overconfident(self):
        counts = [max(0, 10 - i // 40) for i in range(400)]
        hc = calib.hindcast(counts, 90, 14, runs=300)
        r85 = [r for r in hc["table"] if r["level"] == 0.85][0]
        self.assertLess(r85["hit_rate"], 0.3)
        self.assertGreaterEqual(r85["stated"], 0.85)

    def test_block_bootstrap_on_constant(self):
        rng = random.Random(1)
        self.assertEqual(set(calib.simulate_block([3] * 50, 14, 100, rng)), {42})
        self.assertEqual(set(calib.simulate_block([3] * 50, 28, 100, rng)), {84})

    def test_iid_poisson_is_roughly_calibrated(self):
        rng = random.Random(5)
        counts = [calib.poisson(rng, 2.0) for _ in range(730)]
        hc = calib.hindcast(counts, 90, 14, runs=500)
        r95 = [r for r in hc["table"] if r["level"] == 0.95][0]
        self.assertGreater(r95["hit_rate"], 0.8)

    def test_summary_and_predictions_shape(self):
        rng = random.Random(3)
        series = {f"P{i}": [calib.poisson(rng, 1.5) for _ in range(400)] for i in range(3)}
        res = job.analyze(series, 400, runs=100)
        self.assertIn("A_h14", res)
        preds = job.check_predictions(res)
        self.assertIn("P1_A_h14_085_mean_hit_below_0.80", preds)


if __name__ == "__main__":
    unittest.main()
