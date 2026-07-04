#!/usr/bin/env python
"""Run a hand-picked set of eval questions through the real pipeline and save
full question/answer/confidence/decision data for the demo site.

Usage: python scripts/generate_showcase.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline import SupportPipeline

EVAL_SET_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_set.jsonl"
OUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "showcase-data.json"

# A spread across categories and both decision types: clean deflects across a
# few topics, plus escalations for a billing dispute, a security incident, a
# prompt-injection attempt, and an out-of-scope feature request.
SHOWCASE_IDS = ["E003", "E041", "E058", "E076", "E081", "E094", "E086"]


def main():
    eval_items = {}
    with EVAL_SET_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                eval_items[item["id"]] = item

    pipeline = SupportPipeline()
    showcase = []

    for eid in SHOWCASE_IDS:
        item = eval_items[eid]
        result = pipeline.resolve(item["question"])
        showcase.append({
            "id": eid,
            "category": item["category"],
            "question": item["question"],
            "answer": result.answer,
            "confidence": round(result.confidence, 2),
            "escalate": result.escalate,
            "escalate_reason": result.escalate_reason,
            "sources": result.sources,
            "latency_ms": round(result.latency_ms, 0),
        })
        print(f"{eid}: {'ESCALATE' if result.escalate else 'DEFLECT'} (conf={result.confidence:.2f})")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(showcase, indent=2))
    print(f"\nWrote {len(showcase)} showcase examples to {OUT_PATH}")


if __name__ == "__main__":
    main()
