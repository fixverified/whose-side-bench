"""Write half the candidate cases with an OpenAI model, so case authorship can be compared."""

import json
from pathlib import Path

import yaml
from openai import OpenAI

MODEL = "gpt-6-luna"
PER_FAMILY = 6
FIRST_ROUND = [
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
]
SECOND_ROUND = ["unpaid_amount", "informal_change", "misapplied_payment", "settlement_message", "ambiguous_term"]
OUT = Path("data/candidates/gpt.yaml")
SPEC = Path("docs/CASE_SPEC.md").read_text()

cases = yaml.safe_load(OUT.read_text()) if OUT.exists() else []
families = SECOND_ROUND if cases else FIRST_ROUND
client = OpenAI()
for family in families:
    response = client.responses.create(
        model=MODEL,
        input=(
            f"{SPEC}\n\nWrite {PER_FAMILY} new cases in the `{family}` family, following every rule exactly. "
            "Make them differ from each other and from the example. Use amounts that end in unusual digits. "
            'Return JSON only, in the form {"cases": ["case text", ...]}.'
        ),
        text={"format": {"type": "json_object"}},
    )
    texts = json.loads(response.output_text)["cases"]
    if len(texts) != PER_FAMILY:
        raise RuntimeError(f"{family}: got {len(texts)} cases")
    for text in texts:
        cases.append({"id": f"g{len(cases) + 1:03d}", "family": family, "author": MODEL, "text": text})
    print(family, "done", flush=True)
OUT.write_text(yaml.safe_dump(cases, sort_keys=False, allow_unicode=True, width=120))
print("wrote", len(cases))
