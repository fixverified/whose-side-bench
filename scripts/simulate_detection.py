"""Simulate how often the design detects a planted effect at the strictest Holm step."""

import numpy as np

from whose_side_bench.analysis import crossed_bootstrap, estimates, two_sided_p

SIZES = {"power_company": 4, "power_government": 4, "politics": 6, "placebo": 4}
CASES = 14
TESTS = 8
names = [name for name, size in SIZES.items() for _ in range(size)]
INDEXES = {name: np.array([i for i, value in enumerate(names) if value == name]) for name in SIZES}
rng = np.random.default_rng(5)


def detection(key, effect, spread, runs=40):
    hits = 0
    for _ in range(runs):
        table = np.zeros((len(names), CASES))
        for index, name in enumerate(names):
            planted = effect if (key == "politics" and name == "politics") or (key == "power" and name.startswith("power")) else 0
            rate = np.clip(0.5 + planted + rng.normal(0, spread), 0.01, 0.99)
            table[index] = rng.binomial(1, rate, (2, CASES)).mean(axis=0) - 0.5
        estimate = estimates(table, INDEXES)
        draws = crossed_bootstrap(table, INDEXES, reps=1000)
        if two_sided_p(draws[key]) * TESTS < 0.05 and abs(estimate[key]) >= 0.05:
            hits += 1
    return hits / runs


for key in ("politics", "power"):
    for spread in (0.04, 0.08):
        print(key, spread, {effect: round(detection(key, effect, spread), 2) for effect in (0.10, 0.15, 0.20, 0.25, 0.30)}, flush=True)
