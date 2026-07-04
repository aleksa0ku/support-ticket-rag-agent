#!/usr/bin/env python
"""Run the 100-question eval set through the pipeline and report metrics.

Usage: python scripts/run_eval.py [--limit N] [--out eval_results/results.jsonl]

Metrics reported:
  - Deflection rate: % of tickets resolved without a human
  - Escalation-decision accuracy / precision / recall (vs. the human-labeled
    should_deflect field in the eval set)
  - Citation accuracy: for correctly auto-resolved tickets, did the agent cite
    the right help-center doc
  - First-response time: agent latency vs. an assumed human first-response baseline
  - Cost per ticket: agent (token-based estimate) vs. an assumed human-ticket cost
"""
import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.pipeline import SupportPipeline

EVAL_SET_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_set.jsonl"

# Approximate list prices, USD per million tokens (input, output). Verify against
# https://platform.claude.com/docs/en/pricing before relying on these for real budgeting.
PRICING = {
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}
ASSUMED_HUMAN_FIRST_RESPONSE_HOURS = 4.0


def load_eval_set() -> list[dict]:
    items = []
    with EVAL_SET_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = PRICING.get(settings.generation_model, (5.00, 25.00))
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N eval items")
    parser.add_argument("--out", default="eval_results/results.jsonl", help="Where to write per-item results")
    args = parser.parse_args()

    eval_items = load_eval_set()
    if args.limit:
        eval_items = eval_items[: args.limit]

    pipeline = SupportPipeline()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tp = fp = tn = fn = 0
    citation_correct = citation_checked = 0
    total_agent_cost = 0.0
    total_latency_ms = 0.0
    results = []

    for i, item in enumerate(eval_items, 1):
        start = time.perf_counter()
        result = pipeline.resolve(item["question"])
        wall_ms = (time.perf_counter() - start) * 1000

        predicted_deflect = not result.escalate
        expected_deflect = item["should_deflect"]

        if predicted_deflect and expected_deflect:
            tp += 1
        elif predicted_deflect and not expected_deflect:
            fp += 1
        elif not predicted_deflect and not expected_deflect:
            tn += 1
        else:
            fn += 1

        if predicted_deflect and expected_deflect and item.get("expected_doc_ids"):
            citation_checked += 1
            if set(result.sources) & set(item["expected_doc_ids"]):
                citation_correct += 1

        agent_cost = estimate_cost_usd(result.input_tokens, result.output_tokens)
        total_agent_cost += agent_cost
        total_latency_ms += wall_ms

        results.append({
            "id": item["id"],
            "question": item["question"],
            "expected_deflect": expected_deflect,
            "predicted_deflect": predicted_deflect,
            "correct": predicted_deflect == expected_deflect,
            "confidence": round(result.confidence, 3),
            "escalate_reason": result.escalate_reason,
            "sources": result.sources,
            "expected_doc_ids": item.get("expected_doc_ids", []),
            "latency_ms": round(wall_ms, 1),
            "agent_cost_usd": round(agent_cost, 5),
        })
        print(f"[{i}/{len(eval_items)}] {item['id']}: "
              f"{'DEFLECT' if predicted_deflect else 'ESCALATE'} "
              f"(expected {'DEFLECT' if expected_deflect else 'ESCALATE'}) "
              f"conf={result.confidence:.2f}")

    with out_path.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    n = len(eval_items)
    accuracy = (tp + tn) / n if n else 0.0
    deflection_rate = (tp + fp) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    citation_accuracy = citation_correct / citation_checked if citation_checked else float("nan")
    avg_agent_cost = total_agent_cost / n if n else 0.0
    avg_latency_s = (total_latency_ms / n) / 1000 if n else 0.0

    # Blended cost per ticket: agent cost is always incurred; human cost is only
    # incurred for tickets the agent escalates.
    predicted_escalations = n - (tp + fp)
    blended_cost_per_ticket = (
        avg_agent_cost + (predicted_escalations / n) * settings.human_ticket_cost_usd if n else 0.0
    )

    print("\n" + "=" * 60)
    print("EVAL RESULTS")
    print("=" * 60)
    print(f"Eval set size:              {n}")
    print(f"Deflection rate:            {deflection_rate:.1%}  ({tp + fp}/{n} auto-resolved)")
    print(f"Escalation-decision accuracy:{accuracy:.1%}")
    print(f"  Precision (of auto-resolved, % that should have been): {precision:.1%}")
    print(f"  Recall (of resolvable tickets, % correctly auto-resolved): {recall:.1%}")
    print(f"Citation accuracy (on correct auto-resolutions): {citation_accuracy:.1%} "
          f"({citation_correct}/{citation_checked})")
    print(f"Confusion — TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"Avg agent latency:          {avg_latency_s:.2f}s  "
          f"(vs. assumed human first response of {ASSUMED_HUMAN_FIRST_RESPONSE_HOURS:.0f}h)")
    print(f"Avg agent cost per ticket:  ${avg_agent_cost:.4f}  (model: {settings.generation_model})")
    print(f"Blended cost per ticket:    ${blended_cost_per_ticket:.4f}  "
          f"(vs. ${settings.human_ticket_cost_usd:.2f} flat human cost)")
    print(f"\nPer-item results written to {out_path}")


if __name__ == "__main__":
    main()
