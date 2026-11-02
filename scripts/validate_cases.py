"""Check candidate cases against the mechanical rules in docs/CASE_SPEC.md."""

import argparse
import collections
import re
import sys

import yaml

from whose_side_bench.casecheck import problems

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("files", nargs="+")
args = parser.parse_args()

bad = 0
amounts = collections.Counter()
seen = set()
for path in args.files:
    cases = yaml.safe_load(open(path))
    print(path, len(cases), dict(sorted(collections.Counter(case.get("family") for case in cases).items())))
    for case in cases:
        issues = problems(case)
        if case["id"] in seen:
            issues.append("duplicate id")
        seen.add(case["id"])
        amounts.update(re.findall(r"\$[\d,]+", case["text"])[:1])
        if issues:
            bad += 1
            print(f"  {case['id']}: {'; '.join(issues)}")
repeated = {amount: count for amount, count in amounts.items() if count > 1}
print("repeated lead amounts:", repeated or "none")
print("cases with problems:", bad)
sys.exit(1 if bad else 0)
