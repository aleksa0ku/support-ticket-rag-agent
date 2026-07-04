#!/usr/bin/env python
"""Run one named experiment through the eval harness (with LLM-as-judge).

Usage:
  python scripts/run_experiment.py v2               # tuned production config
  python scripts/run_experiment.py v1               # naive baseline
  python scripts/run_experiment.py v2 --limit 10    # quick smoke run
  python scripts/run_experiment.py v2 --no-judge    # skip judge (labels only)

Writes a timestamped result file to eval_results/<run_id>.json.
"""
import argparse
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.presets import get_preset
from eval.runner import run_experiment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("preset", help="Experiment preset name (e.g. v1, v2)")
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N eval items")
    parser.add_argument("--no-judge", action="store_true", help="Skip the LLM-as-judge grading")
    args = parser.parse_args()

    config = get_preset(args.preset)
    if args.no_judge:
        config = replace(config, use_judge=False)

    run = run_experiment(config, limit=args.limit)
    m = run["metrics"]

    print("\n" + "=" * 60)
    print(f"EXPERIMENT: {config.name}  (prompt={config.resolved().prompt_variant}, "
          f"model={config.resolved().model})")
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
