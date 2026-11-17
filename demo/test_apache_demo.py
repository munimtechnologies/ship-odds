# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Offline tests for demo/apache_demo.py (no network)."""
import csv
import io
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apache_demo as ad  # noqa: E402


def raw_fixture():
    cutoff = ad.day_index(ad.parse_time("2026-06-01"))
    hist = []
    for d in range(1, 120):
        day = ad.iso_day(cutoff - d)
        hist.append({"key": f"X-{d}", "summary": f"Fix  thing\n{d}", "type": "Bug" if d % 2 else "Improvement",
                     "created": f"{ad.iso_day(cutoff - d - 5)}T08:00:00.000+0000",
                     "resolved": f"{day}T10:30:00.000+0000", "resolution": "Fixed"})
    opened = [{"key": f"X-{500 + i}", "summary": 'Quote "me", please', "type": "Task",
               "created": "2026-05-01T09:00:00.000+0000",
               "resolved": "2026-06-20T09:00:00.000+0000" if i < 4 else None, "resolution": None}
              for i in range(5)]
    return {"project": "X", "version": {"name": "1.2.0", "releaseDate": "2026-06-29"},
            "release_day": cutoff + 28, "cutoff_day": cutoff, "cutoff": "2026-06-01",
            "lead_days": 28, "history": hist, "open": opened}


class Helpers(unittest.TestCase):
    def test_parse_time_forms(self):
        a = ad.parse_time("2026-01-02T10:00:00.000+0000")
        b = ad.parse_time("2026-01-02T12:00:00.000+0200")
        self.assertEqual(a, b)
        self.assertEqual(ad.parse_time("2026-01-02"), datetime(2026, 1, 2, tzinfo=timezone.utc))
        self.assertEqual(ad.iso_day(ad.day_index(a)), "2026-01-02")

    def test_open_at_cutoff(self):
        cut = ad.parse_time("2026-06-01")
        self.assertTrue(ad.open_at({"created": "2026-05-01T00:00:00.000+0000", "resolved": None}, cut))
        self.assertTrue(ad.open_at({"created": "2026-05-01T00:00:00.000+0000", "resolved": "2026-06-01T00:00:00.000+0000"}, cut))
        self.assertFalse(ad.open_at({"created": "2026-05-01T00:00:00.000+0000", "resolved": "2026-05-31T23:59:00.000+0000"}, cut))
        self.assertFalse(ad.open_at({"created": "2026-06-02T00:00:00.000+0000", "resolved": None}, cut))

    def test_types_and_summary(self):
        self.assertEqual(ad.jira_type("Bug"), "Bug")
        self.assertEqual(ad.jira_type("New Feature"), "Story")
        self.assertEqual(ad.jira_type("Sub-task"), "Task")
        self.assertEqual(ad.clean_summary("a\n  b"), "a b")
        self.assertEqual(len(ad.clean_summary("x" * 500)), 240)


class Forecast(unittest.TestCase):
    def test_constant_pace(self):
        cutoff = 20000
        days = [cutoff - d for d in range(1, 91) for _ in range(2)]  # 2 a day
        f = ad.forecast_at(days, cutoff, 10, cutoff + 4)  # 5 days available -> 10 items
        self.assertEqual(f["probability"], 1.0)
        self.assertEqual(f["finished_in_window"], 180)
        self.assertEqual(ad.forecast_at(days, cutoff, 10, cutoff + 3)["probability"], 0.0)
        self.assertEqual(f["p50"], ad.iso_day(cutoff + 4))

    def test_window_excludes_cutoff_day(self):
        cutoff = 20000
        f = ad.forecast_at([cutoff, cutoff + 1], cutoff, 3, cutoff + 10)
        self.assertIsNone(f["probability"])
        self.assertEqual(f["finished_in_window"], 0)


class Csv(unittest.TestCase):
    def test_shift_and_columns(self):
        raw = raw_fixture()
        text, info = ad.make_csv(raw, "2026-12-01")
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(rows[0][:6], ["Summary", "Issue Type", "Status", "Resolution", "Created", "Resolved"])
        self.assertEqual(info["rows"], len(rows) - 1)
        self.assertEqual(info["rows"], 119 + 5)
        self.assertEqual(info["shift_days"], (datetime(2026, 12, 1) - datetime(2026, 6, 1)).days)
        self.assertEqual(info["release_moves_to"], "2026-12-29")
        anchor = datetime(2026, 12, 1)
        done = [r for r in rows[1:] if r[2] == "Done"]
        todo = [r for r in rows[1:] if r[2] == "To Do"]
        self.assertEqual((len(done), len(todo)), (119, 5))
        for r in done:
            created = datetime.strptime(r[4], "%Y-%m-%d %H:%M")
            resolved = datetime.strptime(r[5], "%Y-%m-%d %H:%M")
            self.assertLessEqual(created, resolved)
            self.assertLess(resolved, anchor, "no finished item may land on or after the import day")
            self.assertEqual(r[3], "Done")
        self.assertEqual(done[0][5], "2026-11-30 10:30")  # one day before the cutoff, kept one day before the anchor
        for r in todo:
            self.assertEqual((r[3], r[5], r[6]), ("", "", "1.2.0"))
            self.assertLess(datetime.strptime(r[4], "%Y-%m-%d %H:%M"), anchor)
        self.assertEqual(todo[0][0], 'Quote "me", please')
        self.assertIn("https://issues.apache.org/jira/browse/X-1 ", done[0][8])
        self.assertIn("moved forward by 183 days", done[0][8])

    def test_outcome(self):
        o = ad.outcome(raw_fixture())
        self.assertEqual(o["open_at_cutoff"], 5)
        self.assertEqual(o["resolved_by_release_day"], 4)
        self.assertEqual(o["still_unresolved_now"], 1)
        self.assertIsNone(o["last_resolved"])

    def test_cli_csv(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            rp = os.path.join(d, "raw.json")
            with open(rp, "w") as f:
                json.dump(raw_fixture(), f)
            out = os.path.join(d, "demo.csv")
            self.assertEqual(ad.main(["csv", "--raw", rp, "--anchor", "2026-12-01", "--out", out]), 0)
            with open(out, "rb") as f:
                head = f.read(3)
            self.assertNotEqual(head, b"\xef\xbb\xbf", "no BOM")


if __name__ == "__main__":
    unittest.main()
