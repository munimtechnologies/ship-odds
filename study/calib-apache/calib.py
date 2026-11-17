# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Hindcast calibration of Monte Carlo throughput forecasts (Python twin of Ship Odds' core).

Same procedure as src/core/forecast.js `hindcast` in github.com/munimtechnologies/ship-odds,
plus a moving-block bootstrap variant. Standard library only.
"""
import math
import random
import re
from datetime import datetime, timezone

DAY = 86400


def parse_time(s):
    """Jira timestamp ('2025-01-02T10:00:00.000+0000') -> POSIX seconds."""
    s = s.strip()
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).timestamp()


def day_index(ts):
    return int(math.floor(ts / DAY))


def iso_to_day(iso_date):
    return day_index(datetime.strptime(iso_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


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


def simulate_iid(samples, horizon, runs, rng):
    return sorted(sum(rng.choices(samples, k=horizon)) for _ in range(runs))


def simulate_block(samples, horizon, runs, rng, block=7):
    n = len(samples)
    if n < block:
        return simulate_iid(samples, horizon, runs, rng)
    prefix = [0]
    for v in samples:
        prefix.append(prefix[-1] + v)
    starts = n - block + 1
    out = []
    for _ in range(runs):
        total = 0
        d = 0
        while d < horizon:
            s = rng.randrange(starts)
            take = min(block, horizon - d)
            total += prefix[s + take] - prefix[s]
            d += take
        out.append(total)
    out.sort()
    return out


def hindcast(counts, window, horizon, method="iid", step=7, levels=(0.5, 0.7, 0.85, 0.95), runs=2000, seed=7):
    """counts[i] = items finished on day i (i = 0 oldest). Origins t in [window, len - horizon], newest first."""
    rng = random.Random(seed)
    sim = simulate_block if method == "block" else simulate_iid
    per = {L: {"n": 0, "hits": 0, "stated": 0.0} for L in levels}
    origins = skipped = 0
    t = len(counts) - horizon
    while t >= window:
        samples = counts[t - window:t]
        if sum(samples) == 0:
            skipped += 1
            t -= step
            continue
        origins += 1
        totals = sim(samples, horizon, runs, rng)
        actual = sum(counts[t:t + horizon])
        for L in levels:
            x = quantile(totals, 1 - L)
            ge = sum(1 for v in totals if v >= x)
            p = per[L]
            p["n"] += 1
            p["stated"] += ge / runs
            p["hits"] += 1 if actual >= x else 0
        t -= step
    table = []
    for L in levels:
        p = per[L]
        table.append({
            "level": L,
            "n": p["n"],
            "stated": p["stated"] / p["n"] if p["n"] else None,
            "hit_rate": p["hits"] / p["n"] if p["n"] else None,
        })
    return {"origins": origins, "skipped": skipped, "table": table}


def poisson(rng, lam):
    """Knuth's method; fine for small lam."""
    limit = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1
