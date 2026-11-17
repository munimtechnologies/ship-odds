# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Real history for a Ship Odds demo site, from a public Apache Jira project.

Two steps, standard library only:

  1. fetch  (needs network; run once):
       python apache_demo.py fetch --out-dir out
     Picks one Apache project and one of its recently released fix versions such
     that, 28 days before the release (the "cutoff"), 15-60 of the version's
     issues were still open and the project had resolved 200-1500 issues as
     Fixed in the year before the cutoff. Writes out/demo_raw.json: that year of
     finished issues, the version's issues open at the cutoff, what really
     happened to them afterwards, and the forecast Ship Odds' model gives at the
     cutoff (a Python twin of src/core/forecast.js).

  2. csv  (offline; run on the day of the import):
       python apache_demo.py csv --raw out/demo_raw.json --anchor 2026-12-01 --out demo.csv
     Moves every date forward by the same number of whole days so the cutoff
     lands on --anchor (the import day, not later), and writes a CSV for Jira's
     admin CSV importer (old experience). Map Resolution AND Resolved (Date
     Resolved), otherwise Jira drops the resolution dates. Date format:
     yyyy-MM-dd HH:mm.

Limits, said plainly in the demo: Apache sets fixVersion in hindsight, so issues
that were moved to a later version are missing from the open set, and the open
set is "what eventually shipped in this version", not what the team planned
28 days before. The demo shows the app working on real history; the evidence for
whether its odds are trustworthy is the calibration study in study/calib-apache.
"""
import argparse
import csv
import io
import json
import math
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://issues.apache.org/jira/rest/api/2"
BROWSE = "https://issues.apache.org/jira/browse/"
UA = "ShipOdds-demo-builder/0.1 (MV2 of Munim, Inc.; mv2@munimtech.com; github.com/munimtechnologies/ship-odds)"
CANDIDATES = [
    "CALCITE", "PARQUET", "AVRO", "ARTEMIS", "NIFI", "HUDI", "IOTDB", "IGNITE",
    "SOLR", "CAMEL", "KAFKA", "FLINK", "HBASE", "HIVE", "ZOOKEEPER", "ORC",
]
LEAD_DAYS = 28
OPEN_RANGE = (15, 60)
HISTORY_RANGE = (200, 1500)
RELEASED_FROM, RELEASED_TO = "2026-03-01", "2026-11-10"
WINDOW = 90
DAY = 86400
JIRA_DATE_FMT = "%Y-%m-%d %H:%M"


# ---------------------------------------------------------------- pure helpers

def parse_time(s):
    """Jira timestamp ('2025-01-02T10:00:00.000+0000') -> aware UTC datetime."""
    s = s.strip()
    if len(s) == 10:
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if s.endswith("Z"):
        s = s[:-1] + "+0000"
    if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def day_index(dt):
    return int(math.floor(dt.timestamp() / DAY))


def iso_day(day):
    return (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=day)).strftime("%Y-%m-%d")


def open_at(issue, cutoff_dt):
    """Did the issue exist and was it unresolved at the cutoff?"""
    created = parse_time(issue["created"])
    resolved = issue.get("resolved")
    return created < cutoff_dt and (resolved is None or parse_time(resolved) >= cutoff_dt)


def daily_counts(days, start_day, n_days):
    out = [0] * n_days
    for d in days:
        if start_day <= d < start_day + n_days:
            out[d - start_day] += 1
    return out


def quantile(sorted_vals, q):
    """Nearest-rank quantile, identical to the JS version."""
    n = len(sorted_vals)
    idx = min(n - 1, max(0, math.ceil(q * n) - 1))
    return sorted_vals[idx]


def simulate_days_to_finish(samples, remaining, runs, rng, max_days=3650):
    """Python twin of simulateDaysToFinish in src/core/forecast.js (iid bootstrap)."""
    out = []
    for _ in range(runs):
        done = d = 0
        while done < remaining and d < max_days:
            done += samples[rng.randrange(len(samples))]
            d += 1
        out.append(d if done >= remaining else math.inf)
    out.sort()
    return out


def forecast_at(history_resolved_days, cutoff_day, remaining, target_day, window=WINDOW, runs=10000, seed=1):
    """P(all `remaining` done by the end of target_day), simulated from the window before cutoff_day."""
    samples = daily_counts(history_resolved_days, cutoff_day - window, window)
    if sum(samples) == 0 or remaining <= 0:
        return {"probability": 1.0 if remaining <= 0 else None, "finished_in_window": sum(samples)}
    days = simulate_days_to_finish(samples, remaining, runs, random.Random(seed))
    allowed = target_day - cutoff_day + 1
    p = sum(1 for d in days if d <= allowed) / runs

    def date_at(q):
        d = quantile(days, q)
        return iso_day(cutoff_day + d - 1) if d != math.inf else None

    return {
        "probability": round(p, 4),
        "finished_in_window": sum(samples),
        "per_week": round(sum(samples) / window * 7, 2),
        "p50": date_at(0.5), "p85": date_at(0.85), "p95": date_at(0.95),
    }


def jira_type(apache_type):
    t = (apache_type or "").lower()
    if t == "bug":
        return "Bug"
    if t in ("new feature", "improvement", "wish"):
        return "Story"
    return "Task"


def clean_summary(s, limit=240):
    s = " ".join((s or "").split())
    return s if len(s) <= limit else s[: limit - 3] + "..."


def shift_fmt(ts, shift_days):
    return (parse_time(ts) + timedelta(days=shift_days)).strftime(JIRA_DATE_FMT)


def make_csv(raw, anchor_iso):
    """Rows for Jira's CSV importer. The cutoff moves to anchor_iso; nothing lands after it."""
    cutoff_day = raw["cutoff_day"]
    anchor_day = day_index(parse_time(anchor_iso))
    shift = anchor_day - cutoff_day
    version = raw["version"]["name"]
    note = (f"Copied from {{url}} (Apache Software Foundation, public issue tracker) for a Ship Odds demo. "
            f"All dates are moved forward by {shift} days.")
    header = ["Summary", "Issue Type", "Status", "Resolution", "Created", "Resolved", "Fix Version", "Labels", "Description"]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    n = 0
    for it in raw["history"]:
        w.writerow([clean_summary(it["summary"]), jira_type(it["type"]), "Done", "Done",
                    shift_fmt(it["created"], shift), shift_fmt(it["resolved"], shift), "",
                    "apache-demo", note.format(url=BROWSE + it["key"])])
        n += 1
    for it in raw["open"]:
        w.writerow([clean_summary(it["summary"]), jira_type(it["type"]), "To Do", "",
                    shift_fmt(it["created"], shift), "", version,
                    "apache-demo", note.format(url=BROWSE + it["key"])])
        n += 1
    return buf.getvalue(), {"rows": n, "shift_days": shift, "cutoff_moves_to": anchor_iso,
                            "release_moves_to": iso_day(raw["release_day"] + shift), "version": version}


# ---------------------------------------------------------------- network

def get(path, params=None, sleep=1.0):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        time.sleep(sleep)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):
                return {"error": e.code}
            time.sleep(10 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (attempt + 1))
    return {"error": "gave up"}


def search(jql, fields, sleep, cap=3000):
    out, start = [], 0
    while True:
        res = get("/search", {"jql": jql, "fields": ",".join(fields), "startAt": start, "maxResults": 1000}, sleep)
        if "error" in res:
            return None, res["error"]
        issues = res.get("issues", [])
        for i in issues:
            f = i.get("fields") or {}
            out.append({
                "key": i["key"],
                "summary": f.get("summary") or "",
                "type": (f.get("issuetype") or {}).get("name"),
                "created": f.get("created"),
                "resolved": f.get("resolutiondate"),
                "resolution": (f.get("resolution") or {}).get("name"),
            })
        start += len(issues)
        if not issues or start >= res.get("total", 0) or start >= cap:
            return out, None


def try_project(key, sleep, log):
    versions = get(f"/project/{key}/versions", None, sleep)
    if isinstance(versions, dict):
        log.append({"project": key, "skip": f"versions error {versions.get('error')}"})
        return None
    recent = [v for v in versions if v.get("released") and v.get("releaseDate")
              and RELEASED_FROM <= v["releaseDate"] <= RELEASED_TO]
    recent.sort(key=lambda v: v["releaseDate"], reverse=True)
    for v in recent[:3]:
        release_day = day_index(parse_time(v["releaseDate"]))
        cutoff_day = release_day - LEAD_DAYS
        cutoff_dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=cutoff_day)
        name = v["name"].replace('"', '\\"')
        issues, err = search(f'project = {key} AND fixVersion = "{name}"',
                             ["summary", "issuetype", "created", "resolutiondate", "resolution"], sleep)
        if err is not None:
            log.append({"project": key, "version": v["name"], "skip": f"search error {err}"})
            continue
        opened = [i for i in issues if i["created"] and open_at(i, cutoff_dt)]
        entry = {"project": key, "version": v["name"], "release": v["releaseDate"], "in_version": len(issues), "open_at_cutoff": len(opened)}
        if not OPEN_RANGE[0] <= len(opened) <= OPEN_RANGE[1]:
            log.append({**entry, "skip": "open count out of range"})
            continue
        since = iso_day(cutoff_day - 365)
        hist, err = search(f'project = {key} AND resolution = Fixed AND resolved >= "{since}" AND resolved < "{iso_day(cutoff_day)}"',
                           ["summary", "issuetype", "created", "resolutiondate", "resolution"], sleep)
        if err is not None or hist is None:
            log.append({**entry, "skip": f"history error {err}"})
            continue
        hist = [h for h in hist if h["created"] and h["resolved"]]
        entry["history"] = len(hist)
        if not HISTORY_RANGE[0] <= len(hist) <= HISTORY_RANGE[1]:
            log.append({**entry, "skip": "history size out of range"})
            continue
        log.append({**entry, "chosen": True})
        return {"project": key, "version": {"name": v["name"], "releaseDate": v["releaseDate"]},
                "release_day": release_day, "cutoff_day": cutoff_day, "cutoff": iso_day(cutoff_day),
                "lead_days": LEAD_DAYS, "history": hist, "open": opened}
    if not recent:
        log.append({"project": key, "skip": "no version released in range"})
    return None


def outcome(raw):
    """What really happened to the open set after the cutoff (resolved dates as recorded)."""
    days = [day_index(parse_time(i["resolved"])) for i in raw["open"] if i.get("resolved")]
    still_open = sum(1 for i in raw["open"] if not i.get("resolved"))
    done_by_release = sum(1 for d in days if d <= raw["release_day"])
    return {
        "open_at_cutoff": len(raw["open"]),
        "resolved_by_release_day": done_by_release,
        "still_unresolved_now": still_open,
        "last_resolved": iso_day(max(days)) if days and not still_open else None,
        "note": "fixVersion is assigned in hindsight, so this set is biased toward items that did ship in this version.",
    }


def cmd_fetch(args):
    os.makedirs(args.out_dir, exist_ok=True)
    log, raw = [], None
    for key in CANDIDATES:
        raw = try_project(key, args.sleep, log)
        print(json.dumps(log[-1]) if log else key, flush=True)
        if raw:
            break
    with open(os.path.join(args.out_dir, "candidates.json"), "w") as f:
        json.dump(log, f, indent=1)
    if not raw:
        print("NO_DEMO_PROJECT_FOUND")
        return 1
    hist_days = [day_index(parse_time(h["resolved"])) for h in raw["history"]]
    raw["forecast_at_cutoff"] = forecast_at(hist_days, raw["cutoff_day"], len(raw["open"]), raw["release_day"])
    raw["outcome"] = outcome(raw)
    with open(os.path.join(args.out_dir, "demo_raw.json"), "w") as f:
        json.dump(raw, f, indent=1)
    sample_csv, info = make_csv(raw, iso_day(raw["cutoff_day"]))  # unshifted copy, for checking
    with open(os.path.join(args.out_dir, "demo_unshifted.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(sample_csv)
    summary = {k: raw[k] for k in ("project", "version", "cutoff", "lead_days")}
    summary.update(history=len(raw["history"]), open=len(raw["open"]), forecast_at_cutoff=raw["forecast_at_cutoff"],
                   outcome=raw["outcome"], csv=info)
    with open(os.path.join(args.out_dir, "demo_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    return 0


def cmd_csv(args):
    with open(args.raw, encoding="utf-8") as f:
        raw = json.load(f)
    text, info = make_csv(raw, args.anchor)
    with open(args.out, "w", encoding="utf-8", newline="") as f:  # plain UTF-8, no BOM
        f.write(text)
    print(json.dumps(info, indent=1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--out-dir", default="out")
    f.add_argument("--sleep", type=float, default=1.0)
    c = sub.add_parser("csv")
    c.add_argument("--raw", required=True)
    c.add_argument("--anchor", required=True, help="YYYY-MM-DD, the import day (cutoff moves here)")
    c.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return cmd_fetch(args) if args.cmd == "fetch" else cmd_csv(args)


if __name__ == "__main__":
    raise SystemExit(main())
