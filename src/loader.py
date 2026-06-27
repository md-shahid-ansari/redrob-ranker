import gzip
import json
from pathlib import Path
from typing import Iterator, Dict, Any

CANDIDATES_PATH = Path("data/candidates.jsonl.gz")

def load_candidates_stream() -> Iterator[Dict[str, Any]]:
    """
    Generator that yields one candidate dict at a time.
    """
    if not CANDIDATES_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {CANDIDATES_PATH}")

    with gzip.open(CANDIDATES_PATH, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def load_candidates_list(limit=None):
    """
    Load all candidates into a list (use only for small testing).
    """
    candidates = []
    for i, c in enumerate(load_candidates_stream()):
        if limit is not None and i >= limit:
            break
        candidates.append(c)
    return candidates

def get_candidate_ids():
    """Return list of all candidate_ids (efficient)."""
    ids = []
    for c in load_candidates_stream():
        ids.append(c["candidate_id"])
    return ids

if __name__ == "__main__":
    # Quick test: count candidates
    count = 0
    for _ in load_candidates_stream():
        count += 1
        if count % 10000 == 0:
            print(f"Loaded {count} candidates")
    print(f"Total candidates: {count}")