#!/usr/bin/env python
"""End-to-end A/B demo: naive baseline (v1) vs tuned production prompt (v2).

Runs both configs through the eval harness (with LLM-as-judge), compares
them, runs the regression gate, writes a markdown report, and emits a
compact JSON the demo site reads.

Usage: python scripts/run_ab_demo.py [--limit N]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.compare import compare
from eval.gate import check_gate
from eval.presets import get_preset
from eval.report import render_markdown
from eval.runner import run_experiment

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "eval_results"
SITE_DATA = ROOT / "docs" / "eval-data.json"


def _metric_map(cmp: dict) -> list[dict]:
    return [
        {
            "metric": d["metric"],
            "baseline": d["baseline"],
            "candidate": d["candidate"],
            "delta": d["delta"],
            "higher_is_better": d["higher_is_better"],
        }
        for d in cmp["metric_deltas"]
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    print(">>> Running BASELINE (v1, naive prompt)...")
    baseline = run_experiment(get_preset("v1"), limit=args.limit)
    print("\n>>> Running CANDIDATE (v2, tuned prompt)...")
    candidate = run_experiment(get_preset("v2"), limit=args.limit)

    cmp = compare(baseline, candidate)
    report = render_markdown(cmp)
    (RESULTS_DIR / "comparison.md").write_text(report)
    print("\n" + report)

    # Direction check: here v2 is the improvement, so run the gate the other
    # way (v2 baseline vs v1 candidate) to demonstrate it CATCHING a regression.
    passed_fwd, _ = check_gate(baseline, candidate)
    passed_rev, violations = check_gate(candidate, baseline)
    print(f"Gate (v1→v2, the real change): {'PASS' if passed_fwd else 'FAIL'}")
    print(f"Gate (v2→v1, simulating a regression): "
          f"{'PASS' if passed_rev else 'FAIL'} — {len(violations)} violation(s)")

    site = {
        "baseline": {
            "name": "v1 — naive prompt",
            "description": "No escalation policy, no prompt-injection guardrails.",
            "metrics": baseline["metrics"],
        },
        "candidate": {
            "name": "v2 — tuned prompt",
            "description": "Explicit escalation policy + injection protection.",
            "metrics": candidate["metrics"],
        },
        "deltas": _metric_map(cmp),
        "regression_count": len(cmp["regressions"]),
        "improvement_count": len(cmp["improvements"]),
        "improvements_sample": cmp["improvements"][:6],
        "gate_catches_regression": not passed_rev,
        "gate_violations": violations,
    }
    SITE_DATA.write_text(json.dumps(site, indent=2))
    print(f"\nSite data written to {SITE_DATA}")
    print(f"Markdown report written to {RESULTS_DIR / 'comparison.md'}")


if __name__ == "__main__":
    main()
