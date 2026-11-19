# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Offline tests for part 3 (no network). Run from this folder: python -m unittest -v"""
import importlib.util
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import job  # noqa: E402
import replicate  # noqa: E402


def poisson_series(lam_of_day, n=730, seed=1):
    rng = random.Random(seed)
    return [replicate.poisson(rng, lam_of_day(d)) for d in range(n)]


class Binomial(unittest.TestCase):
    def test_tail(self):
        self.assertEqual(replicate.binom_upper_tail(10, 0, 0.15), 1.0)
        self.assertEqual(replicate.binom_upper_tail(10, 11, 0.15), 0.0)
        self.assertAlmostEqual(replicate.binom_upper_tail(1, 1, 0.15), 0.15)
        self.assertAlmostEqual(replicate.binom_upper_tail(2, 1, 0.5), 0.75)

    def test_gate(self):
        even = [(i + 0.5) / 50 for i in range(50)]
        self.assertFalse(replicate.gate_open(even))
        self.assertTrue(replicate.gate_open([0.05] * 20 + [0.5] * 20))
        self.assertTrue(replicate.gate_open([0.95] * 20 + [0.5] * 20))
        self.assertFalse(replicate.gate_open([]))


class Prequential(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stable = replicate.prequential(poisson_series(lambda d: 2.0), 90, 14, runs=300)
        cls.drift = replicate.prequential(poisson_series(lambda d: max(0.3, 4.0 * (1 - d / 800)), seed=2), 90, 14,
                                          runs=300)

    def test_shape(self):
        for r in (self.stable, self.drift):
            self.assertGreater(r["evaluated"], 40)
            self.assertEqual(set(r["arms"]), set(replicate.ARMS))
            for arm in replicate.ARMS:
                self.assertEqual([row["level"] for row in r["arms"][arm]["table"]], list(replicate.LEVELS))
                self.assertIsNotNone(r["arms"][arm]["brier"])

    def test_gate_rarely_opens_on_stable_team(self):
        self.assertLessEqual(self.stable["gate_share"], 0.4)

    def test_gate_opens_on_drifting_team_and_helps_85(self):
        self.assertGreater(self.drift["gate_share"], 0.0)
        i = replicate.LEVELS.index(0.85)
        raw = self.drift["arms"]["raw"]["table"][i]["hit"]
        gated = self.drift["arms"]["gated"]["table"][i]["hit"]
        self.assertGreaterEqual(gated, raw)

    def test_gated_equals_raw_when_gate_closed(self):
        r = replicate.prequential([1] * 400, 90, 14, runs=50)  # constant pace: PITs pile up, but check shape only
        if r["gate_share"] == 0:
            self.assertEqual(r["arms"]["gated"]["brier"], r["arms"]["raw"]["brier"])

    def test_summarize(self):
        s = replicate.summarize({"a": self.stable, "b": self.drift})
        self.assertEqual(s["projects"], 2)
        for arm in replicate.ARMS:
            self.assertIn("0.85", s["arms"][arm]["levels"])
            self.assertIn("brier", s["arms"][arm])
        self.assertEqual(s["arms"]["raw"]["share_better_than_raw"], 0.0)

    def test_matches_part2_code(self):
        path = os.path.join(HERE, "..", "recal-apache", "recal.py")
        if not os.path.exists(path):
            self.skipTest("part 2 code not present")
        spec = importlib.util.spec_from_file_location("recal_part2", path)
        recal = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recal)
        counts = poisson_series(lambda d: max(0.3, 3.0 * (1 - d / 900)), seed=3)
        old = recal.prequential(counts, 90, 14, runs=200)
        new = replicate.prequential(counts, 90, 14, runs=200)
        self.assertEqual(old["evaluated"], new["evaluated"])
        self.assertAlmostEqual(old["brier_raw"], new["arms"]["raw"]["brier"], places=12)
        self.assertAlmostEqual(old["brier_cal"], new["arms"]["cal"]["brier"], places=12)
        for i, row in enumerate(old["table"]):
            self.assertAlmostEqual(row["raw_hit"], new["arms"]["raw"]["table"][i]["hit"], places=12)
            self.assertAlmostEqual(row["cal_hit"], new["arms"]["cal"]["table"][i]["hit"], places=12)
            self.assertAlmostEqual(row["cal_stated"], new["arms"]["cal"]["table"][i]["stated"], places=12)


class Fetching(unittest.TestCase):
    def test_v2_paging(self):
        pages = [{"total": 3, "issues": [{"fields": {"resolutiondate": "2025-01-01T10:00:00.000+0000"}}] * 2},
                 {"total": 3, "issues": [{"fields": {"resolutiondate": "2025-01-02T10:00:00.000+0000"}}]}]
        urls = []

        def fake(url, sleep):
            urls.append(url)
            return pages[len(urls) - 1]
        r = job.fetch_v2("https://x", "ABC", "Fixed", 0, fake)
        self.assertEqual(len(r["dates"]), 3)
        self.assertFalse(r["truncated"])
        self.assertIn("startAt=2", urls[1])
        self.assertTrue(urls[0].startswith("https://x/rest/api/2/search?"))

    def test_v3_paging(self):
        pages = [{"issues": [{"fields": {"resolutiondate": "2025-01-01T10:00:00.628+0000"}}], "isLast": False,
                  "nextPageToken": "abc"},
                 {"issues": [{"fields": {"resolutiondate": "2025-01-03T10:00:00.628+0000"}}], "isLast": True}]
        urls = []

        def fake(url, sleep):
            urls.append(url)
            return pages[len(urls) - 1]
        r = job.fetch_v3("https://y", "WFLY", "Done", 0, fake)
        self.assertEqual(len(r["dates"]), 2)
        self.assertIn("nextPageToken=abc", urls[1])
        self.assertTrue(urls[0].startswith("https://y/rest/api/3/search/jql?"))

    def test_error_passes_through(self):
        r = job.fetch_v2("https://x", "NOPE", "Fixed", 0, lambda url, s: {"error": 400})
        self.assertIn("error", r)

    def test_counts(self):
        c = job.to_counts(["2024-11-01T00:30:00.000+0000", "2024-10-31T23:00:00.000+0000",
                           "2026-10-31T23:59:00.000+0000", "2026-11-01T00:00:00.000+0000"])
        self.assertEqual(len(c), 730)
        self.assertEqual(c[0], 1)
        self.assertEqual(c[-1], 1)
        self.assertEqual(sum(c), 2)

    def test_load_series_with_fake_getter(self):
        def fake(url, sleep):
            if "%22WFLY%22" in url or "%22SERVER%22" in url:  # exact keys, not JRASERVER etc.
                d = "2025-%02d-%02dT10:00:00.000+0000"
                issues = [{"fields": {"resolutiondate": d % (1 + i % 12, 1 + i % 28)}} for i in range(250)]
                return {"total": 250, "issues": issues, "isLast": True}
            return {"error": 400}
        series, fetched = job.load_series("", 0, fake)
        self.assertEqual(sorted(series), ["mongodb:SERVER", "redhat:WFLY"])
        self.assertIn("error", fetched["atlassian:JRACLOUD"])


class Grading(unittest.TestCase):
    def test_inconclusive_below_minimum(self):
        res = {"A_h14": {"summary": {"projects": 3}}, "A_h28": {"summary": {"projects": 3}}}
        self.assertIn("inconclusive", job.check(res))

    def test_grades(self):
        def summ(raw_gap, cal_gap, gated_gap, b):
            def lv(gap):
                return {"0.85": {"stated": 0.88, "hit": 0.88 - gap, "gap": gap, "abs_gap": abs(gap),
                                 "share_below": 0.8, "sharpness": 1.0}}
            return {"projects": 12, "arms": {"raw": {"levels": lv(raw_gap), "brier": b[0]},
                                             "cal": {"levels": lv(cal_gap), "brier": b[1]},
                                             "gated": {"levels": lv(gated_gap), "brier": b[2]},
                                             "k40": {"levels": lv(cal_gap), "brier": b[3]}}}
        res = {"A_h14": {"summary": summ(0.08, 0.04, 0.05, (0.18, 0.181, 0.178, 0.179))},
               "A_h28": {"summary": summ(0.12, 0.06, 0.07, (0.2, 0.2, 0.2, 0.2))}}
        p = job.check(res)
        self.assertEqual("".join("Y" if v["held"] else "N" for v in p.values()), "YYYYYYY")


if __name__ == "__main__":
    unittest.main()
