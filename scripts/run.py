"""Run verdicts for chosen cases, role pairs and models. Resumes from existing output."""

import argparse
import collections
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from whose_side_bench.core import call_case, design

MODELS = {
    "gpt": ("openai/gpt-6.1-sol", None),
    "claude": ("anthropic/claude-opus-5", None),
    "glm": ("openrouter/z-ai/glm-5.3", "Wafer"),
    "grok": ("openrouter/x-ai/grok-4.3", None),
}
SEED = 20261102
PRICES_PER_MILLION = {
    "gpt": (2.0, 10.0),
    "claude": (5.0, 25.0),
    "glm": (0.08, 3.6),
    "grok": (1.25, 2.5),
}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
parser.add_argument("--cases", nargs="+", required=True, help="YAML case files")
parser.add_argument("--case-ids", nargs="*", help="Limit to these case ids")
parser.add_argument("--pairs", nargs="*", help="Role pair ids. Omit for all pairs")
parser.add_argument("--screen", action="store_true", help="Use only the Party A and Party B screening pair")
parser.add_argument("--out-dir", required=True)
parser.add_argument("--workers", type=int, default=15)
parser.add_argument("--budget", type=float, required=True, help="Stop starting calls once estimated dollars reach this")
args = parser.parse_args()

cases = [case for path in args.cases for case in yaml.safe_load(open(path))]
if args.case_ids:
    cases = [case for case in cases if case["id"] in set(args.case_ids)]
roles = yaml.safe_load(open("data/roles.yaml"))
pairs = [roles["screen"]] if args.screen else roles["pairs"]
if args.pairs:
    pairs = [pair for pair in pairs if pair["id"] in set(args.pairs)]
case_by_id = {case["id"]: case for case in cases}
pair_by_id = {pair["id"]: pair for pair in pairs}
out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)


spent = [0.0]
spent_lock = threading.Lock()


def row_cost(name, row):
    prompt_price, output_price = PRICES_PER_MILLION[name]
    return ((row["prompt_tokens"] or 0) * prompt_price + (row["completion_tokens"] or 0) * output_price) / 1e6


for name in args.models:
    path = out_dir / f"{name}.jsonl"
    if path.exists():
        spent[0] += sum(row_cost(name, json.loads(line)) for line in path.read_text().splitlines())


def run_model(name):
    model, provider = MODELS[name]
    path = out_dir / f"{name}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            done.add((row["case"], row["pair"], row["assignment"], row["order_index"]))
    planned = design(list(case_by_id), list(pair_by_id))
    stale = done - set(planned)
    if stale:
        raise SystemExit(f"{path} has {len(stale)} rows outside this design. Refusing to resume.")
    jobs = [job for job in planned if job not in done]
    random.Random(SEED).shuffle(jobs)
    lock = threading.Lock()

    def work(job):
        case, pair, assignment, order = job
        if spent[0] >= args.budget:
            return job, "budget reached"
        try:
            row = call_case(model, case_by_id[case], pair_by_id[pair], assignment, order, provider=provider)
        except Exception as error:  # noqa: BLE001 - API errors get re-queued
            return job, f"{type(error).__name__}: {str(error)[:150]}"
        with spent_lock:
            spent[0] += row_cost(name, row)
        with lock, path.open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        return None

    last_errors = collections.Counter()
    results = []
    for _ in range(5):
        if not jobs or spent[0] >= args.budget:
            break
        with ThreadPoolExecutor(args.workers) as pool:
            results = [result for result in pool.map(work, jobs) if result]
        jobs = [job for job, _ in results]
        last_errors = collections.Counter(error for _, error in results)
    if jobs:
        results = results or [(job, "budget reached") for job in jobs]
        with (out_dir / f"{name}.failures.jsonl").open("w") as handle:
            for job, error in results:
                handle.write(json.dumps({"job": job, "error": error}) + "\n")
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    print(
        name,
        "rows:", len(rows),
        "failing:", len(jobs),
        "status:", dict(collections.Counter(row["status"] for row in rows)),
        "returned:", dict(collections.Counter(row["returned_model"] for row in rows)),
        "hosts:", dict(collections.Counter(row["provider"] for row in rows)),
        "errors:", dict(last_errors.most_common(2)),
        flush=True,
    )


with ThreadPoolExecutor(len(args.models)) as outer:
    list(outer.map(run_model, args.models))
print(f"estimated dollars for this output folder: {spent[0]:.3f}")
