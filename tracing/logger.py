
import json
import os
import time

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "runs.jsonl")


def log_run(question: str, result: dict) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": time.time(),
        "question": question,
        "answer": result.get("answer"),
        "data_row_count": (result.get("data") or {}).get("row_count"),
        "trace": result.get("trace"),
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")