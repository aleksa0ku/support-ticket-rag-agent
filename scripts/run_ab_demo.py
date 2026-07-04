#!/usr/bin/env python
"""A/B regression demo: production config vs a proposed change.

Runs both configs through agent-eval-kit (with LLM-as-judge), compares them,
runs the regression gate (metric tolerances + a zero-tolerance safety rule),
writes a markdown report, and emits the compact JSON the demo site reads.

Default pairing tells the "harness catches a bad change before deploy" story:
baseline = v2 (tuned production); candidate = aggressive (loosened config that
chases a higher deflection rate and ships risky answers).

Usage:
  python scripts/run_ab_demo.py                          # v2 vs aggressive, both fresh
  python scripts/run_ab_demo.py --baseline-file <path>   # reuse a cached baseline run
  python scripts/run_ab_demo.py --baseline v2 --candidate v1
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_eval_kit import check_gate, compare, load_run, render_markdown
from agent_eval_kit.gate import safety_category_check

from evals import scoring
from evals.harness import RESULTS_DIR, run_preset

SITE_DATA = Path(__file__).resolve().parent.parent / "docs" / "eval-data.json"

DESCRIPTIONS = {
    "v2": "Tuned prompt with an explicit escalation policy + injection guardrails, calibrated confidence threshold.",
    "v1": "No escalation guidance and no injection guardrails.",
    "aggressive": "Escalation guidance dropped and the confidence threshold loosened to chase a higher deflection rate.",
}


def _load_or_run(preset: str, file: str | None, limit: int | None) -> dict:
    if file:
        path = Path(file)
        run = load_run(path if path.exists() else RESULTS_DIR / file)
        print(f">>> Reusing cached run: {run['run_id']}")
        return run
    print(f">>> Running {preset}...")
    return run_preset(preset, limit=limit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="v2")
    parser.add_argument("--candidate", default="aggressive")
    parser.add_argument("--baseline-file", default=None)
    parser.add_argument("--candidate-file", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    baseline = _load_or_run(args.baseline, args.baseline_file, args.limit)
    candidate = _load_or_run(args.candidate, args.candidate_file, args.limit)

    cmp = compare(baseline, candidate, scoring.TRACKED, scoring.HIGHER_IS_BETTER)
    report = render_markdown(cmp, labels=scoring.LABELS)
    (RESULTS_DIR / "comparison.md").write_text(report)
    print("\n" + report)

    safety_check = safety_category_check(scoring.SAFETY_CATEGORIES, is_incident=scoring.is_safety_incident)
    passed, violations = check_gate(
        baseline, candidate,
        tolerances=scoring.TOLERANCES,
        higher_is_better=scoring.HIGHER_IS_BETTER,
        custom_checks=[safety_check],
    )
    b_name, c_name = baseline["config"]["name"], candidate["config"]["name"]
    print(f"Gate ({b_name} → {c_name}): {'PASS' if passed else 'FAIL'} — {len(violations)} violation(s)")

    site = {
        "baseline": {"name": f"{b_name} — production", "description": DESCRIPTIONS.get(b_name, ""),
                     "metrics": baseline["metrics"]},
        "candidate": {"name": f"{c_name} — proposed change", "description": DESCRIPTIONS.get(c_name, ""),
                      "metrics": candidate["metrics"]},
        "deltas": cmp["metric_deltas"],
        "regression_count": len(cmp["regressions"]),
        "improvement_count": len(cmp["improvements"]),
        "gate_passed": passed,
        "gate_catches_regression": not passed,
        "gate_violations": violations,
        "safety_incidents": [v for v in violations if v.get("type") == "safety"],
    }
    SITE_DATA.write_text(json.dumps(site, indent=2))
    print(f"\nSite data written to {SITE_DATA}")


if __name__ == "__main__":
    main()
