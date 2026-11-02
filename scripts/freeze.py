"""Record hashes of the plan, materials and code before the main run. Refuses to overwrite."""

import datetime
import hashlib
from pathlib import Path

FILES = [
    "docs/PREREGISTRATION.md",
    "docs/CASE_SPEC.md",
    "data/roles.yaml",
    "data/cases.yaml",
    "data/case_review.yaml",
    "data/case_review_gpt.yaml",
    "src/whose_side_bench/core.py",
    "src/whose_side_bench/analysis.py",
    "src/whose_side_bench/casecheck.py",
    "scripts/run.py",
    "scripts/select_cases.py",
    "scripts/analyze.py",
]
OUT = Path("docs/FREEZE.txt")

if OUT.exists():
    raise SystemExit(f"{OUT} already exists.")
if Path("data/votes").exists():
    raise SystemExit("data/votes already exists, so this would not be a pre-run freeze.")
lines = [f"Frozen before the main run: {datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')}"]
lines += [f"{hashlib.sha256(Path(path).read_bytes()).hexdigest()}  {path}" for path in FILES]
OUT.write_text("\n".join(lines) + "\n")
print(OUT.read_text())
