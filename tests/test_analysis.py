import math

import numpy as np

from whose_side_bench.analysis import crossed_bootstrap, design_problems, estimates, holm, lean_table, role_table, two_sided_p

SIZES = {"power_company": 4, "power_government": 4, "politics": 6, "placebo": 4}
names = [name for name, size in SIZES.items() for _ in range(size)]
INDEXES = {name: np.array([i for i, value in enumerate(names) if value == name]) for name in SIZES}


def planted(power=0.0, politics=0.0, seed=1, cases=40, calls=40):
    rng = np.random.default_rng(seed)
    rates = {"power_company": power, "power_government": power, "politics": politics, "placebo": 0}
    table = np.zeros((len(names), cases))
    for index, name in enumerate(names):
        table[index] = rng.binomial(calls, 0.5 + rates[name], cases) / calls - 0.5
    return table


def test_recovers_power_without_politics():
    result = estimates(planted(power=0.1), INDEXES)
    assert abs(result["power"] - 0.1) < 0.02 and abs(result["politics"]) < 0.02


def test_recovers_politics_without_power():
    result = estimates(planted(politics=0.15), INDEXES)
    assert abs(result["power"]) < 0.02 and abs(result["politics"] - 0.15) < 0.02


def test_company_distrust_does_not_register_as_politics():
    table = planted()
    table[INDEXES["power_company"]] += 0.2
    result = estimates(table, INDEXES)
    assert abs(result["politics"]) < 0.02
    assert abs(result["power_company"] - 0.2) < 0.02 and abs(result["power_government"]) < 0.02


def test_bootstrap_detects_effect_and_not_null():
    effect = crossed_bootstrap(planted(power=0.12), INDEXES, reps=500)
    null = crossed_bootstrap(planted(), INDEXES, reps=500)
    assert two_sided_p(effect["power"]) < 0.01
    assert two_sided_p(null["power"]) > 0.01


def test_undefined_draws_never_look_significant():
    table = planted()
    table[INDEXES["politics"]] = np.nan
    draws = crossed_bootstrap(table, INDEXES, reps=50)
    assert math.isnan(two_sided_p(draws["politics"]))
    assert holm({"a": float("nan"), "b": 0.01}) == {"b": 0.02, "a": 1.0}


def test_holm_keeps_order_and_caps():
    assert holm({"a": 0.01, "b": 0.04, "c": 0.5}) == {"a": 0.03, "b": 0.08, "c": 0.5}


def row(direction, side, status="valid", pair="p", case="c"):
    return {"status": status, "pair": pair, "case": case, "assignment": direction, "winner_side": side}


def test_missing_direction_makes_the_unit_undefined():
    table = lean_table([row("focus_claims", "focus"), row("other_claims", None, "extra_content")], ["p"], ["c"])
    assert math.isnan(table[0, 0])


def test_lean_averages_directions():
    assert lean_table([row("focus_claims", "focus"), row("other_claims", "other")], ["p"], ["c"])[0, 0] == 0
    assert lean_table([row("focus_claims", "focus"), row("other_claims", "focus")], ["p"], ["c"])[0, 0] == 0.5


def test_role_table_separates_role_from_facts():
    same_role = [row("focus_claims", "focus"), row("other_claims", "focus")]
    same_facts = [row("focus_claims", "focus"), row("other_claims", "other")]
    assert role_table(same_role, ["p"], ["c"])[0, 0] == 1
    assert role_table(same_facts, ["p"], ["c"])[0, 0] == 0


def test_design_problems_finds_duplicates_and_unknowns():
    row_one = {"case": "c", "pair": "p", "assignment": "focus_claims", "order_index": 0}
    expected = {("c", "p", "focus_claims", 0), ("c", "p", "other_claims", 0)}
    assert design_problems([row_one, row_one], expected) == {"missing": 1, "duplicates": 1, "unknown": 0}
