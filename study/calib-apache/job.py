# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Pre-registered study (see PREREGISTRATION.md): calibration of Monte Carlo throughput
forecasts on public Apache Jira projects. Reads only issue keys and resolution dates."""
import argparse
import json
import os
import random
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

import calib

BASE = "https://issues.apache.org/jira/rest/api/2/search"
UA = "ShipOdds-calibration-study/0.1 (MV2 of Munim, Inc.; mv2@munimtech.com; github.com/munimtechnologies/ship-odds)"
START, END = "2024-11-01", "2026-11-01"
CANDIDATES = [
    "KAFKA", "SPARK", "FLINK", "HIVE", "HADOOP", "HDFS", "YARN", "MAPREDUCE", "HBASE", "CASSANDRA",
    "IGNITE", "SOLR", "ZOOKEEPER", "CALCITE", "NIFI", "PHOENIX", "DRILL", "IMPALA", "HUDI", "TEZ",
    "STORM", "CAMEL", "AMQ", "ARTEMIS", "KARAF", "WICKET", "SLING", "OAK", "CXF", "PDFBOX",
    "TIKA", "LANG", "IO", "COLLECTIONS", "OPENJPA", "DERBY", "KYLIN", "IOTDB", "DOXIA", "SHIRO",
    "FINERACT", "OFBIZ", "JCLOUDS", "QPID", "PROTON", "DIRMINA", "AVRO", "PARQUET", "ORC", "THRIFT",
]
VARIANTS = {"A": ("iid", 90), "B": ("iid", 30), "C": ("iid", 180), "D": ("block", 91)}
HORIZONS = (14, 28)
LEVELS = (0.5, 0.7, 0.85, 0.95)
MIN_ISSUES = 200


def get(params, sleep):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        time.sleep(sleep)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return {"error": e.code, "body": e.read()[:300].decode("utf-8", "replace")}
            if e.code == 429 or e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (attempt + 1))
    return {"error": "gave up"}


def fetch_project(key, sleep):
    jql = f'project = {key} AND resolution = Fixed AND resolved >= "{START}" AND resolved < "{END}" ORDER BY resolved ASC'
    dates, start_at, total = [], 0, None
    while True:
        res = get({"jql": jql, "fields": "resolutiondate", "startAt": start_at, "maxResults": 1000}, sleep)
        if "error" in res:
            return {"error": res}
        total = res.get("total", 0)
        issues = res.get("issues", [])
        for it in issues:
            rd = (it.get("fields") or {}).get("resolutiondate")
            if rd:
                dates.append(rd)
        start_at += len(issues)
        if not issues or start_at >= total or start_at >= 20000:
            break
    return {"total": total, "dates": dates}


def summarize(rows):
    """rows: per-project hindcast tables -> equal-weight mean hit and stated per level."""
    out = {}
    for L in LEVELS:
        hits = [r["hit_rate"] for t in rows for r in t if r["level"] == L and r["hit_rate"] is not None]
        stated = [r["stated"] for t in rows for r in t if r["level"] == L and r["stated"] is not None]
        if hits:
            out[str(L)] = {
                "projects": len(hits),
                "mean_hit": round(statistics.mean(hits), 4),
                "mean_stated": round(statistics.mean(stated), 4),
                "gap_stated_minus_hit": round(statistics.mean(stated) - statistics.mean(hits), 4),
                "median_hit": round(statistics.median(hits), 4),
                "share_below_stated": round(
                    sum(1 for t in rows for r in t if r["level"] == L and r["hit_rate"] is not None and r["hit_rate"] < r["stated"]) / len(hits), 4),
            }
    return out


def analyze(series, n_days, runs):
    results = {}
    for vname, (method, window) in VARIANTS.items():
        for h in HORIZONS:
            tables = {}
            for key, counts in series.items():
                hc = calib.hindcast(counts, window, h, method=method, levels=LEVELS, runs=runs, seed=7)
                if hc["origins"] >= 20:
                    tables[key] = hc
            results[f"{vname}_h{h}"] = {
                "method": method, "window": window, "horizon": h,
                "per_project": {k: v["table"] for k, v in tables.items()},
                "origins": {k: v["origins"] for k, v in tables.items()},
                "summary": summarize([v["table"] for v in tables.values()]),
            }
    return results


def check_predictions(res):
    def s(key, L):
        return res[key]["summary"].get(str(L))
    a14, a28, b14, d14 = s("A_h14", 0.85), s("A_h28", 0.85), s("B_h14", 0.85), s("D_h14", 0.85)
    a14_95 = s("A_h14", 0.95)
    if not all([a14, a28, b14, d14, a14_95]):
        return {"error": "missing summaries"}
    return {
        "P1_A_h14_085_mean_hit_below_0.80": {"value": a14["mean_hit"], "held": a14["mean_hit"] < 0.80},
        "P2_A_h14_095_mean_hit_below_0.90": {"value": a14_95["mean_hit"], "held": a14_95["mean_hit"] < 0.90},
        "P3_D_gap_smaller_than_A_gap": {
            "A": abs(a14["gap_stated_minus_hit"]), "D": abs(d14["gap_stated_minus_hit"]),
            "held": abs(d14["gap_stated_minus_hit"]) < abs(a14["gap_stated_minus_hit"])},
        "P4_A_gap_larger_at_h28": {
            "h14": a14["gap_stated_minus_hit"], "h28": a28["gap_stated_minus_hit"],
            "held": a28["gap_stated_minus_hit"] > a14["gap_stated_minus_hit"]},
        "P5_B_gap_larger_than_A": {
            "A": a14["gap_stated_minus_hit"], "B": b14["gap_stated_minus_hit"],
            "held": b14["gap_stated_minus_hit"] > a14["gap_stated_minus_hit"]},
        "P6_half_projects_below_stated": {"share": a14["share_below_stated"], "held": a14["share_below_stated"] >= 0.5},
    }


def synthetic_control(n_days, runs):
    """iid Poisson projects: variant A should be close to calibrated (sanity check of the code)."""
    rng = random.Random(2026)
    series = {f"SYN{i}": [calib.poisson(rng, 0.5 + 0.25 * i) for _ in range(n_days)] for i in range(10)}
    out = {}
    for h in HORIZONS:
        tables = [calib.hindcast(c, 90, h, method="iid", levels=LEVELS, runs=runs)["table"] for c in series.values()]
        out[f"A_h{h}"] = summarize(tables)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--runs", type=int, default=2000)
    ap.add_argument("--max-projects", type=int, default=len(CANDIDATES))
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    start_day, end_day = calib.iso_to_day(START), calib.iso_to_day(END)
    n_days = end_day - start_day

    fetched, series = {}, {}
    for key in CANDIDATES[: args.max_projects]:
        r = fetch_project(key, args.sleep)
        if "error" in r:
            fetched[key] = {"error": str(r["error"])[:300]}
            print(key, "error", fetched[key], flush=True)
            continue
        days = [calib.day_index(calib.parse_time(d)) for d in r["dates"]]
        counts = calib.daily_counts(days, start_day, n_days)
        fetched[key] = {"total": r["total"], "read": len(r["dates"]), "in_range": sum(counts)}
        print(key, fetched[key], flush=True)
        if sum(counts) >= MIN_ISSUES:
            series[key] = counts
    with open(os.path.join(args.out_dir, "daily_counts.json"), "w") as f:
        json.dump({"start": START, "end": END, "series": series}, f)

    control = synthetic_control(n_days, args.runs)
    res = analyze(series, n_days, args.runs) if series else {}
    preds = check_predictions(res) if series else {"error": "no projects kept"}
    out = {"projects_kept": sorted(series), "fetched": fetched, "control": control, "results": res, "predictions": preds}
    with open(os.path.join(args.out_dir, "results.json"), "w") as f:
        json.dump(out, f, indent=1)

    lines = [f"# Calibration hindcast on Apache Jira ({START} to {END})", "",
             f"Projects kept (>= {MIN_ISSUES} Fixed issues): {len(series)}", ""]
    lines.append("| variant | horizon | level | projects | mean stated | mean hit | gap | share below |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for k, v in res.items():
        for L, row in v["summary"].items():
            lines.append(f"| {k.split('_')[0]} ({v['method']}, W={v['window']}) | {v['horizon']} | {L} | {row['projects']} | "
                         f"{row['mean_stated']} | {row['mean_hit']} | {row['gap_stated_minus_hit']} | {row['share_below_stated']} |")
    lines += ["", "## Synthetic iid control (should be near calibrated)", "", "```", json.dumps(control, indent=1), "```",
              "", "## Pre-registered predictions", "", "```", json.dumps(preds, indent=1), "```"]
    with open(os.path.join(args.out_dir, "RESULTS.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
