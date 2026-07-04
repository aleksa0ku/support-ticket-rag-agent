#!/usr/bin/env python
"""Run one named experiment through agent-eval-kit (with LLM-as-judge).

Usage:
  python scripts/run_experiment.py v2               # tuned production config
  python scripts/run_experiment.py aggressive       # the risky change
  python scripts/run_experiment.py v2 --limit 10    # quick smoke run
  python scripts/run_experiment.py v2 --no-judge    # skip judge (labels only)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.harness import get_preset, run_preset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("preset")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    config = get_preset(args.preset)
    run = run_preset(args.preset, limit=args.limit, use_judge=not args.no_judge)
    m = run["metrics"]

    print("\n" + "=" * 60)
    print(f"EXPERIMENT: {config.name}  {config.params}")
    print("=" * 60)
    print(f"Eval set size:              {m['n']}")
    print(f"Deflection rate:            {m['deflection_rate']:.1%}")
    print(f"Escalation-decision acc.:   {m['escalation_accuracy']:.1%}")
    if m.get("precision") is not None:
        print(f"  Precision:                {m['precision']:.1%}")
    if m.get("recall") is not None:
        print(f"  Recall:                   {m['recall']:.1%}")
    if m.get("citation_accuracy") is not None:
        print(f"Citation accuracy:          {m['citation_accuracy']:.1%}")
    if "avg_quality_score" in m:
        print(f"Judge quality score (0-1):  {m['avg_quality_score']:.2f}")
        print(f"Judge pass rate:            {m['quality_pass_rate']:.1%}")
        print(f"  Faithfulness (1-5):       {m['avg_faithfulness']:.2f}")
        print(f"  Helpfulness (1-5):        {m['avg_helpfulness']:.2f}")
        print(f"  Safety (1-5):             {m['avg_safety']:.2f}")
    print(f"Blended cost per ticket:    ${m['blended_cost_usd']:.4f}")
    print(f"\nResults written to {run['_path']}")


if __name__ == "__main__":
    main()
