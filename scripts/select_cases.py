"""Select final cases from the Party A and Party B screen. Never reads role-pair verdicts."""

import collections
import json
import re
import sys
from pathlib import Path

import yaml

from whose_side_bench.casecheck import problems

LOW, HIGH = 0.25, 0.75
MIN_VALID = 7
PER_AUTHOR_FAMILY = 1
TARGET_PER_AUTHOR = 7
AUTHORS = ("claude", "gpt-6-luna")

candidates = [case for path in ("data/candidates/claude.yaml", "data/candidates/gpt.yaml") for case in yaml.safe_load(open(path))]
reviews = [{entry["id"]: entry["verdict"] for entry in yaml.safe_load(open(path))} for path in ("data/case_review.yaml", "data/case_review_gpt.yaml")]
rows = [json.loads(line) for path in Path("data/screen").glob("*.jsonl") for line in path.read_text().splitlines()]
wins, counts = collections.Counter(), collections.Counter()
for row in rows:
    if row["status"] == "valid":
        counts[row["case"]] += 1
        wins[row["case"]] += row["claimant_won"]

kept = [case for case in candidates if not problems(case) and all(review.get(case["id"]) == "keep" for review in reviews)]
pool = []
for case in kept:
    if counts[case["id"]] < MIN_VALID:
        continue
    share = wins[case["id"]] / counts[case["id"]]
    if LOW <= share <= HIGH:
        pool.append({**case, "screen_claimant_share": round(share, 3)})
print("passed both reviews:", len(kept), "passed screen:", len(pool))


def amount(case):
    return re.findall(r"\$[\d,]+", case["text"])[0]


selected = []
for author in AUTHORS:
    available = sorted((case for case in pool if case["author"] == author), key=lambda case: (abs(case["screen_claimant_share"] - 0.5), case["id"]))
    taken = []
    used = {amount(case) for case in selected}

    def add(case):
        if case not in taken and amount(case) not in used and len(taken) < TARGET_PER_AUTHOR:
            taken.append(case)
            used.add(amount(case))

    for family in sorted({case["family"] for case in candidates}):
        for case in [case for case in available if case["family"] == family and amount(case) not in used][:PER_AUTHOR_FAMILY]:
            add(case)
    for case in available:
        add(case)
    print(author, "selected", len(taken), "available", len(available), dict(sorted(collections.Counter(case["family"] for case in taken).items())))
    selected += taken
if len(selected) != 2 * TARGET_PER_AUTHOR:
    sys.exit(f"Selected {len(selected)} cases, below the target. Nothing written.")
Path("data/cases.yaml").write_text(yaml.safe_dump(sorted(selected, key=lambda case: case["id"]), sort_keys=False, allow_unicode=True, width=120))
print("families:", dict(sorted(collections.Counter(case["family"] for case in selected).items())))
print("mean screen claimant share:", round(sum(case["screen_claimant_share"] for case in selected) / len(selected), 3))
