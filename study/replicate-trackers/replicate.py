# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Part 3 (see PREREGISTRATION.md): raw, corrected and gated-corrected Monte Carlo throughput odds,
evaluated prequentially (strictly out of sample). Standard library only.

The raw and corrected arms use exactly the same procedure and random-number order as part 2
(study/recal-apache/recal.py), so on the same data they reproduce part 2's numbers. The gate and the
k=40 shrinkage arm use no random numbers.
"""
import bisect
import math
import random

LEVELS = (0.5, 0.7, 0.85, 0.95)
SHRINK_K = 10
SHRINK_K_STRONG = 40
MIN_PITS = 12
MEMORY_DAYS = 365
TAIL = 0.15
GATE_ALPHA = 0.001
ARMS = ("raw", "cal", "gated", "k40")


def quantile(sorted_vals, q):
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


def identity(x):
    return min(1.0, max(0.0, x))


def raw_ge(sorted_totals, x):
    n = len(sorted_totals)
    return (n - count_le(sorted_totals, x - 1)) / n


def corrected_ge(sorted_totals, x, g):
    if x <= 0:
        return 1.0
    n = len(sorted_totals)
    return 1.0 - g(count_le(sorted_totals, x - 1) / n)


def corrected_level_x(sorted_totals, level, g):
    lo, hi = 0, sorted_totals[-1] + 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if corrected_ge(sorted_totals, mid, g) >= level:
            lo = mid
        else:
            hi = mid
    return lo


def binom_upper_tail(n, s, p):
    """P(X >= s) for X ~ Binomial(n, p), exact."""
    if s <= 0:
        return 1.0
    if s > n:
        return 0.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(s, n + 1))


def gate_open(pits, tail=TAIL, alpha=GATE_ALPHA):
    """True if the PIT history shows a clear miss: too many outcomes in the model's slowest `tail`
    or in its fastest `tail` (each tested one-sided, exact binomial, at level alpha)."""
    n = len(pits)
    if n == 0:
        return False
    slow = sum(1 for p in pits if p <= tail)
    fast = sum(1 for p in pits if p >= 1 - tail)
    return binom_upper_tail(n, slow, tail) < alpha or binom_upper_tail(n, fast, tail) < alpha


def prequential(counts, window, horizon, method="iid", step=7, levels=LEVELS, runs=2000, seed=7,
                min_pits=MIN_PITS, memory=MEMORY_DAYS):
    """counts[i] = items finished on day i (0 = oldest). Returns per-arm, per-level results."""
    rng = random.Random(seed)
    urng = random.Random(seed + 1)
    sim = simulate_block if method == "block" else simulate_iid
    origins = []
    t = len(counts) - horizon
    while t >= window:
        origins.append(t)
        t -= step
    origins.reverse()

    history = []
    per = {a: {L: {"n": 0, "hit": 0, "stated": 0.0, "x": 0.0} for L in levels} for a in ARMS}
    brier = {a: 0.0 for a in ARMS}
    n_brier = 0
    evaluated = skipped = gated_on = 0
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
            g10 = make_g(avail, SHRINK_K)
            g40 = make_g(avail, SHRINK_K_STRONG)
            is_open = gate_open(avail)
            gated_on += 1 if is_open else 0
            maps = {"raw": identity, "cal": g10, "gated": g10 if is_open else identity, "k40": g40}
            for L in levels:
                x = quantile(totals, 1 - L)
                hit_raw = 1 if actual >= x else 0
                for arm, g in maps.items():
                    if arm == "raw" or g is identity:
                        y, p_stated = x, raw_ge(totals, x)
                        p_event = raw_ge(totals, x)
                    else:
                        y = corrected_level_x(totals, L, g)
                        p_stated = corrected_ge(totals, y, g)
                        p_event = corrected_ge(totals, x, g)
                    cell = per[arm][L]
                    cell["n"] += 1
                    cell["hit"] += 1 if actual >= y else 0
                    cell["stated"] += p_stated
                    cell["x"] += y
                    brier[arm] += (p_event - hit_raw) ** 2
                n_brier += 1
        history.append((t, pit(totals, actual, urng.random())))

    out = {"evaluated": evaluated, "skipped": skipped, "gate_share": gated_on / evaluated if evaluated else None,
           "arms": {}}
    for arm in ARMS:
        table = []
        for L in levels:
            c = per[arm][L]
            raw_x = per["raw"][L]["x"]
            n = c["n"]
            table.append({"level": L, "n": n,
                          "stated": c["stated"] / n if n else None,
                          "hit": c["hit"] / n if n else None,
                          "sharpness": (c["x"] / raw_x) if n and raw_x > 0 else None})
        out["arms"][arm] = {"table": table, "brier": brier[arm] / n_brier if n_brier else None}
    pits = [p for (_, p) in history]
    out["slow_tail"] = sum(1 for p in pits if p <= TAIL) / len(pits) if pits else None
    return out


def summarize(results, levels=LEVELS):
    """{project: prequential(...)} -> equal-weight means per arm and level, Brier, shares."""
    res = {k: r for k, r in results.items() if r["evaluated"]}
    out = {"projects": len(res), "arms": {}}
    if not res:
        return out
    for arm in ARMS:
        lv = {}
        for i, L in enumerate(levels):
            rows = [r["arms"][arm]["table"][i] for r in res.values() if r["arms"][arm]["table"][i]["n"]]
            if not rows:
                continue
            st = sum(x["stated"] for x in rows) / len(rows)
            hit = sum(x["hit"] for x in rows) / len(rows)
            sh = [x["sharpness"] for x in rows if x["sharpness"] is not None]
            lv[str(L)] = {"projects": len(rows), "stated": round(st, 4), "hit": round(hit, 4),
                          "gap": round(st - hit, 4), "abs_gap": round(abs(st - hit), 4),
                          "share_below": round(sum(1 for x in rows if x["hit"] < x["stated"]) / len(rows), 4),
                          "sharpness": round(sum(sh) / len(sh), 4) if sh else None}
        b = [r["arms"][arm]["brier"] for r in res.values()]
        raw_b = [r["arms"]["raw"]["brier"] for r in res.values()]
        out["arms"][arm] = {"levels": lv, "brier": round(sum(b) / len(b), 5),
                            "share_better_than_raw": round(sum(1 for a, r in zip(b, raw_b) if a < r) / len(b), 4)}
    gs = [r["gate_share"] for r in res.values() if r["gate_share"] is not None]
    out["mean_gate_share"] = round(sum(gs) / len(gs), 4) if gs else None
    return out


def poisson(rng, lam):
    limit = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1
