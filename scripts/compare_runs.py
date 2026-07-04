#!/usr/bin/env python
"""Diff two experiment result files: metric deltas + per-item flips.

Usage:
  python scripts/compare_runs.py <baseline.json> <candidate.json> [--md report.md]

Directory-less names are looked up under eval_results/.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_eval_kit import compare, load_run, render_markdown

from evals import scoring

RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval_results"


def _load(name: str) -> dict:
    path = Path(name)
    return load_run(path if path.exists() else RESULTS_DIR / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("candidate")
    parser.add_argument("--md")
    args = parser.parse_args()

    cmp = compare(_load(args.baseline), _load(args.candidate),
                  scoring.TRACKED, scoring.HIGHER_IS_BETTER)
    report = render_markdown(cmp, labels=scoring.LABELS)
    print(report)
    if args.md:
        Path(args.md).write_text(report)
        print(f"Markdown report written to {args.md}")


if __name__ == "__main__":
    main()
