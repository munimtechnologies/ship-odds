# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Prequential test of PIT recalibration for Monte Carlo throughput forecasts.

Python twin of the correction in Ship Odds 0.2.0 (src/core/forecast.js: pitOf, recalibrator,
correctProbability), evaluated strictly out of sample. See PREREGISTRATION.md. Standard library only.
"""
import bisect
import math
import random

LEVELS = (0.5, 0.7, 0.85, 0.95)
SHRINK_K = 10
MIN_PITS = 12
MEMORY_DAYS = 365


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


def count_le(sorted_vals, x):
    return bisect.bisect_right(sorted_vals, x)


def pit(sorted_totals, actual, u):
    n = len(sorted_totals)
    below = count_le(sorted_totals, actual - 1)
    at_most = count_le(sorted_totals, actual)
    return (below + u * (at_most - below)) / n


def make_g(pits, k=SHRINK_K):
    s = sorted(pits)
    n = len(s)

    def g(x):
        x = min(1.0, max(0.0, x))
        return (bisect.bisect_right(s, x) + k * x) / (n + k)

    return g


def raw_ge(sorted_totals, x):
    """Raw model P(T >= x)."""
    n = len(sorted_totals)
    return (n - count_le(sorted_totals, x - 1)) / n


def corrected_ge(sorted_totals, x, g):
    """Corrected P(T >= x) = 1 - G(F(x - 1)). P(T >= 0) is 1 by definition."""
    if x <= 0:
        return 1.0
    n = len(sorted_totals)
    return 1.0 - g(count_le(sorted_totals, x - 1) / n)


def corrected_level_x(sorted_totals, level, g):
    """Largest whole count Y with corrected P(T >= Y) >= level (0 if none above 0 qualifies)."""
    lo, hi = 0, sorted_totals[-1] + 1  # corrected_ge(hi) = 1 - G(1) = 0 < level
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if corrected_ge(sorted_totals, mid, g) >= level:
            lo = mid
        else:
            hi = mid
    return lo


def prequential(counts, window, horizon, method="iid", step=7, levels=LEVELS, runs=2000, seed=7,
                k=SHRINK_K, min_pits=MIN_PITS, memory=MEMORY_DAYS):
    """counts[i] = items finished on day i (0 = oldest). Returns per-level raw vs corrected results."""
    rng = random.Random(seed)
    urng = random.Random(seed + 1)
    sim = simulate_block if method == "block" else simulate_iid
    origins = []
    t = len(counts) - horizon
    while t >= window:  # same origins as part 1's hindcast, then put in time order
        origins.append(t)
        t -= step
    origins.reverse()

    history = []  # (origin, pit)
    per = {L: {"n": 0, "raw_hit": 0, "raw_stated": 0.0, "cal_hit": 0, "cal_stated": 0.0,
               "raw_x": 0.0, "cal_x": 0.0} for L in levels}
    brier_raw = brier_cal = 0.0
    n_brier = 0
    evaluated = skipped = 0
    for t in origins:
        samples = counts[t - window:t]
        if sum(samples) == 0:
            skipped += 1
            continue
        totals = sim(samples, horizon, runs, rng)
        actual = sum(counts[t:t + horizon])
        avail = [p for (tj, p) in history if tj + horizon <= t and tj >= t - memory]
        if len(avail) >= min_pits:
            evaluated += 1
            g = make_g(avail, k)
            for L in levels:
                x = quantile(totals, 1 - L)
                p_raw = raw_ge(totals, x)
                hit = 1 if actual >= x else 0
                y = corrected_level_x(totals, L, g)
                p_cal = corrected_ge(totals, y, g)
                hit_cal = 1 if actual >= y else 0
                p = per[L]
                p["n"] += 1
                p["raw_hit"] += hit
                p["raw_stated"] += p_raw
                p["cal_hit"] += hit_cal
                p["cal_stated"] += p_cal
                p["raw_x"] += x
                p["cal_x"] += y
                brier_raw += (p_raw - hit) ** 2
                brier_cal += (corrected_ge(totals, x, g) - hit) ** 2
                n_brier += 1
        history.append((t, pit(totals, actual, urng.random())))

    table = []
    for L in levels:
        p = per[L]
        n = p["n"]
        table.append({
            "level": L,
            "n": n,
            "raw_stated": p["raw_stated"] / n if n else None,
            "raw_hit": p["raw_hit"] / n if n else None,
            "cal_stated": p["cal_stated"] / n if n else None,
            "cal_hit": p["cal_hit"] / n if n else None,
            "sharpness": (p["cal_x"] / p["raw_x"]) if n and p["raw_x"] > 0 else None,
        })
    pits = [p for (_, p) in history]
    return {
        "evaluated": evaluated,
        "skipped": skipped,
        "table": table,
        "brier_raw": brier_raw / n_brier if n_brier else None,
        "brier_cal": brier_cal / n_brier if n_brier else None,
        "mean_pit": sum(pits) / len(pits) if pits else None,
        "slow_tail": sum(1 for p in pits if p <= 0.15) / len(pits) if pits else None,
    }


def summarize(results, levels=LEVELS):
    """results: {project: prequential(...)} -> equal-weight summary per level, plus Brier."""
    out = {"projects": len(results), "levels": {}}
    for L in levels:
        rows = [r["table"][levels.index(L)] for r in results.values()]
        rows = [x for x in rows if x["n"]]
        if not rows:
            continue

        def mean(key):
            vals = [x[key] for x in rows if x[key] is not None]
            return sum(vals) / len(vals) if vals else None

        rs, rh, cs, ch = mean("raw_stated"), mean("raw_hit"), mean("cal_stated"), mean("cal_hit")
        out["levels"][str(L)] = {
            "projects": len(rows),
            "raw_stated": round(rs, 4), "raw_hit": round(rh, 4), "raw_gap": round(abs(rs - rh), 4),
            "cal_stated": round(cs, 4), "cal_hit": round(ch, 4), "cal_gap": round(abs(cs - ch), 4),
            "sharpness": None if mean("sharpness") is None else round(mean("sharpness"), 4),
        }
    br = [(r["brier_raw"], r["brier_cal"]) for r in results.values() if r["brier_raw"] is not None]
    if br:
        out["brier_raw"] = round(sum(a for a, _ in br) / len(br), 5)
        out["brier_cal"] = round(sum(b for _, b in br) / len(br), 5)
        out["share_projects_cal_better"] = round(sum(1 for a, b in br if b < a) / len(br), 4)
    return out


def poisson(rng, lam):
    """Knuth's method; fine for small lam."""
    limit = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1
