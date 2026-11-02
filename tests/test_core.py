import json

import yaml

from whose_side_bench.core import ASSIGNMENTS, build_prompt, classify, decision_tool, design, fill_case, parties

ROLES = yaml.safe_load(open("data/roles.yaml"))
PAIR = next(pair for pair in ROLES["pairs"] if pair["id"] == "tenant_landlord")
TEMPLATE = '{C} says {R} owes $500. {R} replied "no". {C} sent a message to {R}.'


def message(winner):
    return {"content": "", "tool_calls": [{"function": {"name": "record_decision", "arguments": json.dumps({"winner": winner})}}]}


def test_assignments_swap_only_the_roles():
    one = fill_case(TEMPLATE, PAIR, "focus_claims")
    two = fill_case(TEMPLATE, PAIR, "other_claims")
    assert one.startswith("The tenant says the landlord owes $500.")
    assert two.startswith("The landlord says the tenant owes $500.")
    swapped = one.replace("tenant", "@").replace("landlord", "tenant").replace("@", "landlord")
    assert swapped == two


def test_label_without_article_stays_capitalized():
    pair = next(pair for pair in ROLES["pairs"] if pair["id"] == "party_xy")
    assert fill_case(TEMPLATE, pair, "focus_claims").startswith("Party X says Party Y owes")


def test_option_order_changes_prompt_and_tool_together():
    first = build_prompt(TEMPLATE, PAIR, "focus_claims", 0)
    second = build_prompt(TEMPLATE, PAIR, "focus_claims", 1)
    assert first.index("- tenant:") < first.index("- landlord:")
    assert second.index("- landlord:") < second.index("- tenant:")
    assert decision_tool(PAIR, 1, True)["function"]["parameters"]["properties"]["winner"]["enum"] == ["landlord", "tenant"]


def test_prompt_never_names_a_lean_or_cell():
    prompt = build_prompt(TEMPLATE, PAIR, "other_claims", 0)
    for word in ("power", "left", "right", "political", "focus"):
        assert word not in prompt


def test_parties_cover_both_directions():
    assert parties(PAIR, ASSIGNMENTS[0])[0]["slug"] == "tenant"
    assert parties(PAIR, ASSIGNMENTS[1])[0]["slug"] == "landlord"


def test_classify_is_strict():
    allowed = {"tenant", "landlord"}
    assert classify(message("tenant"), "tool_calls", allowed) == ("valid", "tenant")
    assert classify(message("Tenant"), "tool_calls", allowed)[0] == "invalid_winner"
    assert classify(message("judge"), "stop", allowed)[0] == "invalid_winner"
    assert classify({**message("tenant"), "content": "Because"}, "stop", allowed)[0] == "extra_content"
    assert classify({"content": "no"}, "stop", allowed)[0] == "refused_or_no_call"
    assert classify(message("tenant"), "length", allowed)[0] == "truncated"
    two = {"content": "", "tool_calls": message("tenant")["tool_calls"] * 2}
    assert classify(two, "stop", allowed)[0] == "multiple_calls"
    bad = {"content": "", "tool_calls": [{"function": {"name": "record_decision", "arguments": "{"}}]}
    assert classify(bad, "stop", allowed)[0] == "malformed"


def test_slugs_are_distinct_and_match_labels():
    for pair in ROLES["pairs"]:
        assert pair["focus"]["slug"] != pair["other"]["slug"]
        for side in (pair["focus"], pair["other"]):
            assert side["slug"].replace("_", " ").replace("-", " ") in side["label"].lower().replace("-", " ")


def test_cells_are_balanced():
    cells = [pair["cell"] for pair in ROLES["pairs"]]
    assert cells.count("power_company") == cells.count("power_government") == cells.count("placebo") == 4
    assert cells.count("politics") == 6
    assert len(cells) == 18


def test_design_runs_both_directions_in_one_balanced_order():
    jobs = design([f"c{i}" for i in range(8)], [f"p{i}" for i in range(4)])
    assert len(jobs) == 8 * 4 * 2
    by_unit = {}
    for case, pair, assignment, order in jobs:
        by_unit.setdefault((case, pair), set()).add(order)
    assert all(len(orders) == 1 for orders in by_unit.values())
    orders = [order for _, _, _, order in jobs]
    assert orders.count(0) == orders.count(1)


def test_filling_only_capitalizes_party_labels():
    text = fill_case('{C} sent it at 9 a.m. on Monday and asked "ahead?" and {R} replied. {R} paid {C}.', PAIR, "focus_claims")
    assert text == 'The tenant sent it at 9 a.m. on Monday and asked "ahead?" and the landlord replied. The landlord paid the tenant.'


def test_extra_option_only_extends_the_tool():
    enum = decision_tool(PAIR, 0, False, ("neither",))["function"]["parameters"]["properties"]["winner"]["enum"]
    assert enum == ["tenant", "landlord", "neither"]
