# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Pre-registered study, part 2 (see PREREGISTRATION.md): does PIT recalibration from a project's own
past make Monte Carlo throughput odds come true at their stated rate? Public Apache Jira, keys and dates only."""
import argparse
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import recal

BASE = "https://issues.apache.org/jira/rest/api/2/search"
UA = "ShipOdds-calibration-study/0.2 (MV2 of Munim, Inc.; mv2@munimtech.com; github.com/munimtechnologies/ship-odds)"
START, END = "2024-11-01", "2026-11-01"
# Same candidates as part 1 (study/calib-apache/job.py).
CANDIDATES = [
    "KAFKA", "SPARK", "FLINK", "HIVE", "HADOOP", "HDFS", "YARN", "MAPREDUCE", "HBASE", "CASSANDRA",
    "IGNITE", "SOLR", "ZOOKEEPER", "CALCITE", "NIFI", "PHOENIX", "DRILL", "IMPALA", "HUDI", "TEZ",
    "STORM", "CAMEL", "AMQ", "ARTEMIS", "KARAF", "WICKET", "SLING", "OAK", "CXF", "PDFBOX",
    "TIKA", "LANG", "IO", "COLLECTIONS", "OPENJPA", "DERBY", "KYLIN", "IOTDB", "DOXIA", "SHIRO",
    "FINERACT", "OFBIZ", "JCLOUDS", "QPID", "PROTON", "DIRMINA", "AVRO", "PARQUET", "ORC", "THRIFT",
]
MIN_ISSUES = 200
MIN_EVALUATED = 20
RUNS = {"A_h14": ("iid", 90, 14), "A_h28": ("iid", 90, 28), "D_h14": ("block", 91, 14)}
CACHE_NAME = "apache_fixed_20241101_20261101.json"


def parse_time(s):
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s.strip())
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).timestamp()


def iso_to_day(iso_date):
    return int(datetime.strptime(iso_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() // 86400)


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


def load_series(data_dir, sleep):
    """Daily Fixed counts per kept project, cached in data_dir so later jobs don't refetch."""
    cache = os.path.join(data_dir, CACHE_NAME) if data_dir else None
    if cache and os.path.exists(cache):
        with open(cache) as f:
            d = json.load(f)
        print("using cached series", cache, flush=True)
        return d["series"], d["fetched"]
    start_day, n_days = iso_to_day(START), iso_to_day(END) - iso_to_day(START)
    series, fetched = {}, {}
    for key in CANDIDATES:
        r = fetch_project(key, sleep)
        if "error" in r:
            fetched[key] = {"error": str(r["error"])[:300]}
            print(key, "error", fetched[key], flush=True)
            continue
        counts = [0] * n_days
        for d in r["dates"]:
            day = int(parse_time(d) // 86400) - start_day
            if 0 <= day < n_days:
                counts[day] += 1
        fetched[key] = {"total": r["total"], "read": len(r["dates"]), "in_range": sum(counts)}
        print(key, fetched[key], flush=True)
        if sum(counts) >= MIN_ISSUES:
            series[key] = counts
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
            r = recal.prequential(counts, window, h, method=method, runs=runs, seed=7)
            if r["evaluated"] >= MIN_EVALUATED:
                per[key] = r
        out[name] = {"method": method, "window": window, "horizon": h, "per_project": per,
                     "summary": recal.summarize(per)}
        print(name, json.dumps(out[name]["summary"]), flush=True)
    return out


def check(res):
    a14 = res["A_h14"]["summary"]
    a28 = res["A_h28"]["summary"]
    l14 = a14["levels"].get("0.85")
    l28 = a28["levels"].get("0.85")
    if not l14 or not l28 or "brier_raw" not in a14:
        return {"error": "missing summaries"}
    return {
        "R1_h14_085_cal_gap_smaller": {"raw_gap": l14["raw_gap"], "cal_gap": l14["cal_gap"],
                                       "held": l14["cal_gap"] < l14["raw_gap"]},
        "R2_h14_085_cal_hit_in_0.80_0.90": {"cal_hit": l14["cal_hit"], "held": 0.80 <= l14["cal_hit"] <= 0.90},
        "R3_h14_brier_lower": {"raw": a14["brier_raw"], "cal": a14["brier_cal"], "held": a14["brier_cal"] < a14["brier_raw"]},
        "R4_h28_085_cal_gap_smaller": {"raw_gap": l28["raw_gap"], "cal_gap": l28["cal_gap"],
                                       "held": l28["cal_gap"] < l28["raw_gap"]},
        "R5_h14_share_projects_better_ge_0.6": {"share": a14["share_projects_cal_better"],
                                                "held": a14["share_projects_cal_better"] >= 0.6},
    }


def controls(runs):
    rng = random.Random(2026)
    iid = {f"SYN{i}": [recal.poisson(rng, 0.5 + 0.25 * i) for _ in range(730)] for i in range(8)}
    drift = {f"DRIFT{i}": [recal.poisson(rng, max(0.3, (3.0 + 0.5 * i) * (1 - d / 900))) for d in range(730)]
             for i in range(8)}
    out = {}
    for name, ser in (("iid", iid), ("drift_down", drift)):
        per = {k: recal.prequential(c, 90, 14, runs=runs) for k, c in ser.items()}
        out[name] = recal.summarize(per)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--runs", type=int, default=2000)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    series, fetched = load_series(args.data_dir, args.sleep)
    ctrl = controls(args.runs)
    print("controls", json.dumps(ctrl), flush=True)
    res = run_all(series, args.runs) if series else {}
    preds = check(res) if series else {"error": "no projects kept"}
    slim = {k: {kk: vv for kk, vv in v.items() if kk != "per_project"} for k, v in res.items()}
    per_project = {k: {p: {"evaluated": r["evaluated"], "brier_raw": r["brier_raw"], "brier_cal": r["brier_cal"],
                           "mean_pit": r["mean_pit"], "slow_tail": r["slow_tail"], "table": r["table"]}
                       for p, r in v["per_project"].items()} for k, v in res.items()}
    with open(os.path.join(args.out_dir, "results.json"), "w") as f:
        json.dump({"projects_kept": sorted(series), "fetched": fetched, "controls": ctrl, "summaries": slim,
                   "per_project": per_project, "predictions": preds}, f, indent=1)

    lines = [f"# Part 2: PIT recalibration, prequential, Apache Jira ({START} to {END})", "",
             f"Projects kept: {len(series)}. Projects per run need >= {MIN_EVALUATED} evaluated origins.", "",
             "| run | level | projects | raw stated | raw hit | raw gap | corrected stated | corrected hit | corrected gap | sharpness |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for name, v in slim.items():
        for L, row in v["summary"]["levels"].items():
            lines.append(f"| {name} | {L} | {row['projects']} | {row['raw_stated']} | {row['raw_hit']} | {row['raw_gap']} | "
                         f"{row['cal_stated']} | {row['cal_hit']} | {row['cal_gap']} | {row['sharpness']} |")
        s = v["summary"]
        if "brier_raw" in s:
            lines.append(f"| {name} | Brier | {s['projects']} | | | {s['brier_raw']} | | | {s['brier_cal']} | "
                         f"better in {s['share_projects_cal_better']} |")
    lines += ["", "## Controls", "", "```", json.dumps(ctrl, indent=1), "```",
              "", "## Pre-registered predictions", "", "```", json.dumps(preds, indent=1), "```"]
    with open(os.path.join(args.out_dir, "RESULTS.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
