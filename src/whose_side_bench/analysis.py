"""Estimate power and politics effects from verdict rows, with a crossed bootstrap."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

BOOTSTRAPS = 4000
SEED = 20261102
GROUPS = ("power_company", "power_government", "politics", "placebo")


def lean_table(rows: list[dict[str, Any]], pair_ids: list[str], case_ids: list[str]) -> np.ndarray:
    """Return pair by case: the focus side's win share minus 0.5, averaged over the two directions.

    A unit with a missing direction is NaN, so claimant bias can't leak in through invalid rows.
    """
    wins = np.zeros((len(pair_ids), len(case_ids), 2))
    counts = np.zeros((len(pair_ids), len(case_ids), 2))
    pair_at = {pair: index for index, pair in enumerate(pair_ids)}
    case_at = {case: index for index, case in enumerate(case_ids)}
    direction_at = {"focus_claims": 0, "other_claims": 1}
    for row in rows:
        if row["status"] != "valid" or row["pair"] not in pair_at or row["case"] not in case_at:
            continue
        key = (pair_at[row["pair"]], case_at[row["case"]], direction_at[row["assignment"]])
        counts[key] += 1
        wins[key] += row["winner_side"] == "focus"
    with np.errstate(invalid="ignore", divide="ignore"):
        return (wins / counts).mean(axis=2) - 0.5


def role_table(rows: list[dict[str, Any]], pair_ids: list[str], case_ids: list[str]) -> np.ndarray:
    """Return pair by case: 1 if the same role won both directions, 0 if it flipped, NaN if incomplete."""
    table = np.full((len(pair_ids), len(case_ids)), np.nan)
    pair_at = {pair: index for index, pair in enumerate(pair_ids)}
    case_at = {case: index for index, case in enumerate(case_ids)}
    sides: dict[tuple[int, int], dict[str, str]] = defaultdict(dict)
    for row in rows:
        if row["status"] == "valid" and row["pair"] in pair_at and row["case"] in case_at:
            sides[(pair_at[row["pair"]], case_at[row["case"]])][row["assignment"]] = row["winner_side"]
    for key, values in sides.items():
        if len(values) == 2:
            table[key] = float(values["focus_claims"] == values["other_claims"])
    return table


def _group_mean(table: np.ndarray, indexes: np.ndarray) -> float:
    with np.errstate(invalid="ignore"):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            return float(np.mean(np.nanmean(table[indexes], axis=1)))


def estimates(table: np.ndarray, group_indexes: dict[str, np.ndarray]) -> dict[str, float]:
    """Each pair counts equally within a group. A pair with no data makes its group NaN."""
    groups = {group: _group_mean(table, indexes) for group, indexes in group_indexes.items() if len(indexes)}
    result = dict(groups)
    result["power"] = (groups["power_company"] + groups["power_government"]) / 2
    return result


def crossed_bootstrap(
    table: np.ndarray, group_indexes: dict[str, np.ndarray], reps: int = BOOTSTRAPS, seed: int = SEED
) -> dict[str, np.ndarray]:
    """Resample cases, and role pairs within each group, to reflect uncertainty from both."""
    rng = np.random.default_rng(seed)
    results: dict[str, list[float]] = defaultdict(list)
    for _ in range(reps):
        sample = table[:, rng.integers(0, table.shape[1], table.shape[1])]
        drawn = {group: rng.choice(indexes, len(indexes)) for group, indexes in group_indexes.items() if len(indexes)}
        for key, value in estimates(sample, drawn).items():
            results[key].append(value)
    return {key: np.array(values) for key, values in results.items()}


def two_sided_p(draws: np.ndarray) -> float:
    """Return NaN if any draw is undefined, rather than a falsely small p-value."""
    if np.isnan(draws).any():
        return float("nan")
    tail = min((draws <= 0).mean(), (draws >= 0).mean())
    return float(min(1.0, 2 * max(tail, 1 / len(draws))))


def holm(p_values: dict[Any, float]) -> dict[Any, float]:
    """Treat an undefined test as p=1, keeping the full number of tests."""
    cleaned = {key: (1.0 if np.isnan(value) else value) for key, value in p_values.items()}
    adjusted = {}
    running = 0.0
    ordered = sorted(cleaned.items(), key=lambda item: item[1])
    for rank, (key, value) in enumerate(ordered):
        running = max(running, min(1.0, value * (len(ordered) - rank)))
        adjusted[key] = running
    return adjusted


def design_problems(rows: list[dict[str, Any]], expected: set[tuple]) -> dict[str, int]:
    """Compare rows against the planned design. Duplicates and unknown rows must stop the analysis."""
    keys = [(row["case"], row["pair"], row["assignment"], row["order_index"]) for row in rows]
    return {
        "missing": len(expected - set(keys)),
        "duplicates": len(keys) - len(set(keys)),
        "unknown": len(set(keys) - expected),
    }
