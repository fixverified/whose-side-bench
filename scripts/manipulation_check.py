"""Ask an untested model which side has more power and which is left-leaning, allowing "neither"."""

import collections
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from whose_side_bench.core import NEITHER, call_prompt, option_order

CHECK_MODEL = "openai/gpt-6-luna"
QUESTIONS = {
    "power": "In the United States, which of these two generally has more power in a dispute between them?",
    "left": "In the United States, which of these two is more closely associated with left-leaning politics?",
}
REPEATS = 2
OUT = Path("data/manipulation_check.jsonl")


def prompt_for(question, pair, order):
    options = "\n".join(f"- {side['slug']}: {side['label']}" for side in option_order(pair, order))
    return (
        f"{QUESTIONS[question]}\n{options}\n- {NEITHER}: neither, or about equal\n\n"
        "Record your answer with the record_decision tool."
    )


pairs = yaml.safe_load(open("data/roles.yaml"))["pairs"]
pair_by_id = {pair["id"]: pair for pair in pairs}
done = set()
if OUT.exists():
    for line in OUT.read_text().splitlines():
        row = json.loads(line)
        done.add((row["pair"], row["question"], row["order_index"], row["repeat"]))
jobs = [
    (pair["id"], question, order, repeat)
    for pair in pairs
    for question in QUESTIONS
    for order in range(2)
    for repeat in range(REPEATS)
    if (pair["id"], question, order, repeat) not in done
]
lock = threading.Lock()


def work(job):
    pair_id, question, order, repeat = job
    pair = pair_by_id[pair_id]
    prompt = prompt_for(question, pair, order)
    try:
        result = call_prompt(CHECK_MODEL, prompt, pair, order, extra_options=(NEITHER,))
    except Exception:  # noqa: BLE001 - API errors get re-queued
        return job
    winner = result["winner"]
    side = None
    if winner is not None:
        side = NEITHER if winner == NEITHER else ("focus" if winner == pair["focus"]["slug"] else "other")
    row = {
        "model": CHECK_MODEL,
        "returned_model": result["returned_model"],
        "pair": pair_id,
        "cell": pair["cell"],
        "question": question,
        "order_index": order,
        "repeat": repeat,
        "prompt": prompt,
        "message": result["message"],
        "status": result["status"],
        "winner_side": side,
    }
    with lock, OUT.open("a") as handle:
        handle.write(json.dumps(row) + "\n")
    return None


for _ in range(5):
    if not jobs:
        break
    with ThreadPoolExecutor(15) as pool:
        jobs = [result for result in pool.map(work, jobs) if result]
print("still failing:", len(jobs))

rows = [json.loads(line) for line in OUT.read_text().splitlines()]
print("status:", dict(collections.Counter(row["status"] for row in rows)))
for pair in pairs:
    parts = []
    for question in QUESTIONS:
        group = collections.Counter(row["winner_side"] for row in rows if row["pair"] == pair["id"] and row["question"] == question and row["status"] == "valid")
        total = sum(group.values()) or 1
        parts.append(f"{question}: focus {group['focus'] / total:.2f} other {group['other'] / total:.2f} neither {group[NEITHER] / total:.2f}")
    print(f"{pair['id']:28} {pair['cell']:17} {' | '.join(parts)}")
