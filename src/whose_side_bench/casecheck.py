"""Mechanical checks for the rules in docs/CASE_SPEC.md."""

import re

FAMILIES = {
    "unpaid_amount",
    "shared_expense",
    "deposit",
    "cancellation_fee",
    "damaged_item",
    "settlement_message",
    "ambiguous_term",
    "missed_deadline",
    "informal_change",
    "misapplied_payment",
}
BANNED = re.compile(
    r"\b(he|she|him|her|his|hers|himself|herself|rent|lease|tenant|landlord|wages?|salary|employee|employer|loan|"
    r"interest|insurance|patient|medical|union|church|farm|school|tuition|passenger|flight|shipping|airline|customer|"
    r"client|vendor|contractor|law|legal|lawsuit|court|statute|attorney|phone call|in person|poor|wealthy|rich|small|"
    r"large|elderly|young|disabled)\b",
    re.IGNORECASE,
)


def problems(case: dict) -> list[str]:
    found = []
    text = case.get("text", "")
    placeholders = set(re.findall(r"\{[^}]*\}", text))
    if placeholders != {"{C}", "{R}"}:
        found.append(f"placeholders {sorted(placeholders)}")
    if text.count("{C}") < 2 or text.count("{R}") < 2:
        found.append("each placeholder must appear at least twice")
    words = len(text.split())
    if not 45 <= words <= 90:
        found.append(f"{words} words")
    if case.get("family") not in FAMILIES:
        found.append(f"family {case.get('family')}")
    if match := BANNED.search(text):
        found.append(f"banned word '{match.group(0)}'")
    if re.search(r"\b(the|a|an)\s+\{[CR]\}", text, re.IGNORECASE):
        found.append("article before placeholder")
    if not re.search(r"\$\d", text):
        found.append("no dollar amount")
    if re.search(r"\{[CR]\}'s", text):
        found.append("possessive placeholder")
    if text.rstrip().endswith("?"):
        found.append("ends with a question")
    return found
