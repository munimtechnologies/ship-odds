# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Pre-registered study, part 3 (see PREREGISTRATION.md): do parts 1 and 2 replicate on four public Jira
trackers not used before, and does correcting only after a clear miss (the gate) beat correcting always?

Reads only issue keys and resolution dates from public, anonymous Jira search APIs, >= 1 s between requests.
Usage: python job.py --out-dir out --data-dir data [--apache-cache ../recal-apache/data/apache_fixed_20241101_20261101.json]
"""
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate  # noqa: E402

UA = "ShipOdds-calibration-study/0.3 (MV2 of Munim, Inc.; mv2@munimtech.com; github.com/munimtechnologies/ship-odds)"
START, END = "2024-11-01", "2026-11-01"
MIN_ISSUES = 200
MIN_EVALUATED = 20
MAX_READ = 20000
MIN_PROJECTS = 10
RUNS = {"A_h14": ("iid", 90, 14), "A_h28": ("iid", 90, 28)}
CACHE_NAME = "trackers_fixed_20241101_20261101.json"

# Fixed on 2026-11-19 before any of these projects' data was fetched (see PREREGISTRATION.md).
TRACKERS = {
    "mongodb": {"base": "https://jira.mongodb.org", "api": "v2", "resolution": "Fixed", "projects": [
        "SERVER", "WT", "TOOLS", "PYTHON", "JAVA", "NODE", "CSHARP", "GODRIVER", "CDRIVER", "CXX", "RUST",
        "PHPLIB", "PHPC", "RUBY", "MOTOR", "COMPASS", "MONGOSH", "DOCS", "SPARK", "KAFKA"]},
    "atlassian": {"base": "https://jira.atlassian.com", "api": "v2", "resolution": "Fixed", "projects": [
        "JRACLOUD", "JSWCLOUD", "CONFCLOUD", "JSDCLOUD", "BCLOUD", "JRASERVER", "JSWSERVER", "CONFSERVER",
        "JSDSERVER", "BSERV"]},
    "jenkins": {"base": "https://issues.jenkins.io", "api": "v2", "resolution": "Fixed", "projects": [
        "JENKINS", "INFRA"]},
    "redhat": {"base": "https://redhat.atlassian.net", "api": "v3", "resolution": "Done", "projects": [
        "WFLY", "WFCORE", "UNDERTOW", "RESTEASY", "ISPN", "JGRP", "ELY", "JBEAP", "OCPBUGS", "RHEL", "CNV",
        "ACM", "OSDOCS", "MTV", "AAP"]},
}


def parse_time(s):
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s.strip())
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).timestamp()


def iso_to_day(iso_date):
    return int(datetime.strptime(iso_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() // 86400)


def get(url, sleep):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        time.sleep(sleep)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404, 410):
                return {"error": e.code, "body": e.read()[:300].decode("utf-8", "replace")}
            if e.code == 429 or e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            return {"error": e.code}
        except (urllib.error.URLError, TimeoutError, ValueError):
            time.sleep(10 * (attempt + 1))
    return {"error": "gave up"}


def jql_for(key, resolution):
    return (f'project = "{key}" AND resolution = "{resolution}" AND resolved >= "{START}" '
            f'AND resolved < "{END}" ORDER BY resolved ASC')


def dates_of(issues):
    out = []
    for it in issues:
        rd = (it.get("fields") or {}).get("resolutiondate")
        if rd:
            out.append(rd)
    return out


def fetch_v2(base, key, resolution, sleep, getter=get):
    """Jira Server/Data Center search: startAt paging, reports a total."""
    jql = jql_for(key, resolution)
    dates, start_at, total = [], 0, None
    while True:
        q = urllib.parse.urlencode({"jql": jql, "fields": "resolutiondate", "startAt": start_at, "maxResults": 1000})
        res = getter(base + "/rest/api/2/search?" + q, sleep)
        if "error" in res:
            return {"error": res}
        total = res.get("total", 0)
        issues = res.get("issues", [])
        dates += dates_of(issues)
        start_at += len(issues)
        if not issues or start_at >= total:
            break
        if start_at >= MAX_READ:
            return {"total": total, "dates": dates, "truncated": True}
    return {"total": total, "dates": dates, "truncated": False}


def fetch_v3(base, key, resolution, sleep, getter=get):
    """Jira Cloud enhanced search: nextPageToken paging, no total."""
    jql = jql_for(key, resolution)
    dates, token = [], None
    while True:
        params = {"jql": jql, "fields": "resolutiondate", "maxResults": 1000}
        if token:
            params["nextPageToken"] = token
        res = getter(base + "/rest/api/3/search/jql?" + urllib.parse.urlencode(params), sleep)
        if "error" in res:
            return {"error": res}
        issues = res.get("issues", [])
        dates += dates_of(issues)
        token = res.get("nextPageToken")
        if res.get("isLast", not token) or not token or not issues:
            break
        if len(dates) >= MAX_READ:
            return {"total": None, "dates": dates, "truncated": True}
    return {"total": len(dates), "dates": dates, "truncated": False}


def to_counts(dates):
    start_day, n_days = iso_to_day(START), iso_to_day(END) - iso_to_day(START)
    counts = [0] * n_days
    for d in dates:
        day = int(parse_time(d) // 86400) - start_day
        if 0 <= day < n_days:
            counts[day] += 1
    return counts


def load_series(data_dir, sleep, getter=get):
    cache = os.path.join(data_dir, CACHE_NAME) if data_dir else None
    if cache and os.path.exists(cache):
        with open(cache) as f:
            d = json.load(f)
        print("using cached series", cache, flush=True)
        return d["series"], d["fetched"]
    series, fetched = {}, {}
    for tname, tr in TRACKERS.items():
        fetch = fetch_v3 if tr["api"] == "v3" else fetch_v2
        for key in tr["projects"]:
            pid = f"{tname}:{key}"
            r = fetch(tr["base"], key, tr["resolution"], sleep, getter)
            if "error" in r:
                fetched[pid] = {"error": str(r["error"])[:300]}
            elif r["truncated"]:
                fetched[pid] = {"excluded": "more than %d issues" % MAX_READ, "read": len(r["dates"])}
            else:
                counts = to_counts(r["dates"])
                fetched[pid] = {"total": r["total"], "read": len(r["dates"]), "in_range": sum(counts)}
                if sum(counts) >= MIN_ISSUES:
                    series[pid] = counts
            print(pid, fetched[pid], flush=True)
    if cache:
        os.makedirs(data_dir, exist_ok=True)
        with open(cache, "w") as f:
            json.dump({"start": START, "end": END, "series": series, "fetched": fetched}, f)
    return series, fetched


def run_all(series, runs):
    out = {}
    for name, (method, window, h) in RUNS.items():
        per = {}
        for key, counts in series.items():
            r = replicate.prequential(counts, window, h, method=method, runs=runs, seed=7)
            if r["evaluated"] >= MIN_EVALUATED:
                per[key] = r
        out[name] = {"method": method, "window": window, "horizon": h, "per_project": per,
                     "summary": replicate.summarize(per)}
        print(name, json.dumps(out[name]["summary"]), flush=True)
    return out


def check(res):
    """Grades T1-T7 exactly as pre-registered."""
    a14, a28 = res["A_h14"]["summary"], res["A_h28"]["summary"]
    n = a14.get("projects", 0)
    if n < MIN_PROJECTS:
        return {"inconclusive": f"only {n} projects kept (pre-registered minimum {MIN_PROJECTS})"}
    raw14 = a14["arms"]["raw"]["levels"]["0.85"]
    raw28 = a28["arms"]["raw"]["levels"]["0.85"]
    cal14 = a14["arms"]["cal"]["levels"]["0.85"]
    gat14 = a14["arms"]["gated"]["levels"]["0.85"]
    b = {arm: a14["arms"][arm]["brier"] for arm in replicate.ARMS}
    return {
        "T1_raw_h14_085_gap_gt_0.03": {"gap": raw14["gap"], "held": raw14["gap"] > 0.03},
        "T2_half_projects_below_stated": {"share": raw14["share_below"], "held": raw14["share_below"] >= 0.5},
        "T3_raw_gap_larger_at_h28": {"h14": raw14["gap"], "h28": raw28["gap"], "held": raw28["gap"] > raw14["gap"]},
        "T4_cal_abs_gap_smaller_than_raw": {"raw": raw14["abs_gap"], "cal": cal14["abs_gap"],
                                            "held": cal14["abs_gap"] < raw14["abs_gap"]},
        "T5_gated_brier_lower_than_cal": {"gated": b["gated"], "cal": b["cal"], "held": b["gated"] < b["cal"]},
        "T6_gated_brier_lower_than_raw": {"gated": b["gated"], "raw": b["raw"], "held": b["gated"] < b["raw"]},
        "T7_gated_abs_gap_smaller_than_raw": {"raw": raw14["abs_gap"], "gated": gat14["abs_gap"],
                                              "held": gat14["abs_gap"] < raw14["abs_gap"]},
    }


def controls(runs):
    rng = random.Random(2026)
    iid = {f"SYN{i}": [replicate.poisson(rng, 0.5 + 0.25 * i) for _ in range(730)] for i in range(8)}
    drift = {f"DRIFT{i}": [replicate.poisson(rng, max(0.3, (3.0 + 0.5 * i) * (1 - d / 900))) for d in range(730)]
             for i in range(8)}
    return {name: replicate.summarize({k: replicate.prequential(c, 90, 14, runs=runs) for k, c in ser.items()})
            for name, ser in (("iid", iid), ("drift_down", drift))}


def apache_exploratory(path, runs):
    """Exploratory, not graded: the same arms on part 2's cached Apache data (the data the gate was suggested by)."""
    with open(path) as f:
        series = json.load(f)["series"]
    per = {}
    for key, counts in series.items():
        r = replicate.prequential(counts, 90, 14, runs=runs, seed=7)
        if r["evaluated"] >= MIN_EVALUATED:
            per[key] = r
    return replicate.summarize(per)


def table_lines(title, summary):
    lines = [f"### {title} ({summary.get('projects', 0)} projects)", "",
             "| arm | level | stated | hit | gap | share below | sharpness |", "|---|---|---|---|---|---|---|"]
    for arm, a in summary.get("arms", {}).items():
        for L, row in a["levels"].items():
            lines.append(f"| {arm} | {L} | {row['stated']} | {row['hit']} | {row['gap']} | {row['share_below']} | "
                         f"{row['sharpness']} |")
        lines.append(f"| {arm} | Brier | | | {a['brier']} | better than raw in {a['share_better_than_raw']} | |")
    lines += ["", f"Mean share of forecasts where the gate was open: {summary.get('mean_gate_share')}", ""]
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--runs", type=int, default=2000)
    ap.add_argument("--apache-cache", default="")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    series, fetched = load_series(args.data_dir, args.sleep)
    ctrl = controls(args.runs)
    print("controls", json.dumps(ctrl), flush=True)
    res = run_all(series, args.runs) if series else {}
    preds = check(res) if series else {"inconclusive": "no projects kept"}
    apache = apache_exploratory(args.apache_cache, args.runs) if args.apache_cache else None
    by_tracker = {}
    if res:
        for tname in TRACKERS:
            sub = {k: v for k, v in res["A_h14"]["per_project"].items() if k.startswith(tname + ":")}
            by_tracker[tname] = replicate.summarize(sub)
    per_project = {k: {p: r for p, r in v["per_project"].items()} for k, v in res.items()}
    slim = {k: {kk: vv for kk, vv in v.items() if kk != "per_project"} for k, v in res.items()}
    with open(os.path.join(args.out_dir, "results.json"), "w") as f:
        json.dump({"projects_kept": sorted(series), "fetched": fetched, "controls": ctrl, "summaries": slim,
                   "by_tracker_A_h14": by_tracker, "apache_exploratory_A_h14": apache,
                   "per_project": per_project, "predictions": preds}, f, indent=1)

    lines = [f"# Part 3: replication on four public Jira trackers ({START} to {END})", "",
             f"Projects kept: {len(series)} (>= {MIN_ISSUES} issues; per run >= {MIN_EVALUATED} evaluated origins).", ""]
    for name, v in slim.items():
        lines += table_lines(name, v["summary"])
    for tname, s in by_tracker.items():
        lines += table_lines(f"A_h14, tracker {tname}", s)
    if apache:
        lines += table_lines("Exploratory: A_h14 on part 2's Apache data", apache)
    lines += ["## Controls", "", "```", json.dumps(ctrl, indent=1), "```",
              "", "## Pre-registered predictions", "", "```", json.dumps(preds, indent=1), "```"]
    with open(os.path.join(args.out_dir, "RESULTS.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    held = "".join("Y" if v.get("held") else "N" for v in preds.values() if isinstance(v, dict))
    a14 = slim.get("A_h14", {}).get("summary", {}).get("arms", {})

    def g(arm, key="hit"):
        try:
            return a14[arm]["levels"]["0.85"][key] if key != "brier" else a14[arm]["brier"]
        except KeyError:
            return None
    print("REPLICATE_LINE: kept=%d raw_hit=%s cal_hit=%s gated_hit=%s brier_raw=%s brier_cal=%s brier_gated=%s "
          "brier_k40=%s T1-7=%s" % (len(series), g("raw"), g("cal"), g("gated"), g("raw", "brier"),
                                    g("cal", "brier"), g("gated", "brier"), g("k40", "brier"), held or "none"),
          flush=True)


if __name__ == "__main__":
    main()
