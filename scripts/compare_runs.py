#!/usr/bin/env python
"""Diff two experiment result files: metric deltas + per-item flips.

Usage:
  python scripts/compare_runs.py <baseline.json> <candidate.json>
  python scripts/compare_runs.py <baseline.json> <candidate.json> --md report.md

If given directory-less names, files are looked up under eval_results/.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.compare import compare
from eval.report import render_markdown

RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval_results"


def _load(name: str) -> dict:
    path = Path(name)
    if not path.exists():
        path = RESULTS_DIR / name
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("candidate")
    parser.add_argument("--md", help="Also write the markdown report to this path")
    args = parser.parse_args()

    cmp = compare(_load(args.baseline), _load(args.candidate))
    report = render_markdown(cmp)
    print(report)

    if args.md:
        Path(args.md).write_text(report)
        print(f"Markdown report written to {args.md}")


if __name__ == "__main__":
    main()
