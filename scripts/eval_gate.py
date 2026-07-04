#!/usr/bin/env python
"""Regression gate: exit non-zero if a candidate run regresses vs a baseline.

Checks metric tolerances AND a zero-tolerance safety rule (no safety-critical
ticket may be auto-resolved when it should escalate). Intended to run
on-demand or from a manually-triggered CI job before promoting a change.

Usage:
  python scripts/eval_gate.py --baseline <baseline.json> --candidate <candidate.json>

Exit codes: 0 = passed, 1 = regressed.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_eval_kit import check_gate, load_run
from agent_eval_kit.gate import safety_category_check

from evals import scoring

RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval_results"


def _load(name: str) -> dict:
    path = Path(name)
    return load_run(path if path.exists() else RESULTS_DIR / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()

    baseline, candidate = _load(args.baseline), _load(args.candidate)
    passed, violations = check_gate(
        baseline, candidate,
        tolerances=scoring.TOLERANCES,
        higher_is_better=scoring.HIGHER_IS_BETTER,
        custom_checks=[safety_category_check(scoring.SAFETY_CATEGORIES, is_incident=scoring.is_safety_incident)],
    )

    print(f"Gate: {baseline['config']['name']} (baseline) vs "
          f"{candidate['config']['name']} (candidate)")
    if passed:
        print("PASS — no regression.")
        sys.exit(0)

    print(f"FAIL — {len(violations)} violation(s):")
    for v in violations:
        if v["type"] == "metric":
            direction = "dropped" if v["higher_is_better"] else "rose"
            print(f"  - metric {v['metric']}: {v['baseline']:.3f} → {v['candidate']:.3f} "
                  f"({direction} {abs(v['delta']):.3f}, tolerance {v['tolerance']:.3f})")
        else:
            print(f"  - safety [{v['category']}] {v['id']}: auto-resolved a ticket that should escalate")
    sys.exit(1)


if __name__ == "__main__":
    main()
