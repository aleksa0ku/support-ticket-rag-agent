#!/usr/bin/env python
"""Regression gate: exit non-zero if a candidate run regresses vs a baseline.

Usage:
  python scripts/eval_gate.py --baseline <baseline.json> --candidate <candidate.json>

Intended to be run on-demand or from a manually-triggered CI job (GitHub
Actions workflow_dispatch) before promoting a prompt/model change — not on
every commit, since each run makes real API calls.

Exit codes: 0 = passed (no regression), 1 = one or more metrics regressed
beyond tolerance.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.gate import check_gate

RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval_results"


def _load(name: str) -> dict:
    path = Path(name)
    if not path.exists():
        path = RESULTS_DIR / name
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()

    baseline, candidate = _load(args.baseline), _load(args.candidate)
    passed, violations = check_gate(baseline, candidate)

    print(f"Gate: {baseline['config']['name']} (baseline) vs "
          f"{candidate['config']['name']} (candidate)")
    if passed:
        print("PASS — no tracked metric regressed beyond tolerance.")
        sys.exit(0)

    print(f"FAIL — {len(violations)} metric(s) regressed:")
    for v in violations:
        direction = "dropped" if v["higher_is_better"] else "rose"
        print(f"  - {v['metric']}: {v['baseline']:.3f} → {v['candidate']:.3f} "
              f"({direction} {abs(v['delta']):.3f}, tolerance {v['tolerance']:.3f})")
    sys.exit(1)


if __name__ == "__main__":
    main()
