#!/usr/bin/env python
"""A/B regression demo: production config vs a proposed change.

Runs a known-good baseline and a candidate config through the eval harness
(with LLM-as-judge), compares them, runs the regression gate, writes a
markdown report, and emits the compact JSON the demo site reads.

The default pairing tells the "harness catches a bad change before deploy"
story: baseline = v2 (tuned production config); candidate = aggressive (a
loosened config that chases a higher deflection rate and ships risky answers).

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

from eval.compare import compare
from eval.gate import check_gate
from eval.presets import get_preset
from eval.report import render_markdown
from eval.runner import run_experiment

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "eval_results"
SITE_DATA = ROOT / "docs" / "eval-data.json"

# Human-facing descriptions per preset for the site data.
DESCRIPTIONS = {
    "v2": "Tuned prompt with an explicit escalation policy + injection guardrails, calibrated confidence threshold.",
    "v1": "No escalation guidance and no injection guardrails.",
    "aggressive": "Escalation guidance dropped and the confidence threshold loosened to chase a higher deflection rate.",
}


def _load_or_run(preset_name: str, file: str | None, limit: int | None) -> dict:
    if file:
        path = Path(file)
        if not path.exists():
            path = RESULTS_DIR / file
        run = json.loads(path.read_text())
        print(f">>> Reusing cached run: {run['run_id']}")
        return run
    print(f">>> Running {preset_name}...")
    return run_experiment(get_preset(preset_name), limit=limit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="v2", help="Baseline preset (known-good)")
    parser.add_argument("--candidate", default="aggressive", help="Candidate preset (the change)")
    parser.add_argument("--baseline-file", default=None, help="Reuse a cached baseline result file")
    parser.add_argument("--candidate-file", default=None, help="Reuse a cached candidate result file")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    baseline = _load_or_run(args.baseline, args.baseline_file, args.limit)
    candidate = _load_or_run(args.candidate, args.candidate_file, args.limit)

    cmp = compare(baseline, candidate)
    report = render_markdown(cmp)
    (RESULTS_DIR / "comparison.md").write_text(report)
    print("\n" + report)

    # Gate the candidate against the baseline: does the proposed change regress?
    passed, violations = check_gate(baseline, candidate)
    print(f"Gate ({baseline['config']['name']} → {candidate['config']['name']}): "
          f"{'PASS' if passed else 'FAIL'} — {len(violations)} violation(s)")

    b_name, c_name = baseline["config"]["name"], candidate["config"]["name"]
    site = {
        "baseline": {
            "name": f"{b_name} — production",
            "description": DESCRIPTIONS.get(b_name, ""),
            "metrics": baseline["metrics"],
        },
        "candidate": {
            "name": f"{c_name} — proposed change",
            "description": DESCRIPTIONS.get(c_name, ""),
            "metrics": candidate["metrics"],
        },
        "deltas": [
            {"metric": d["metric"], "baseline": d["baseline"], "candidate": d["candidate"],
             "delta": d["delta"], "higher_is_better": d["higher_is_better"]}
            for d in cmp["metric_deltas"]
        ],
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
