"""Wires the deflection agent + task scoring into agent-eval-kit."""
import json
from pathlib import Path

from agent_eval_kit import DEFAULT_QUALITY_RUBRIC, ExperimentConfig, Judge, run_experiment

from app.config import settings
from evals.adapter import DeflectionAgent
from evals import scoring

ROOT = Path(__file__).resolve().parent.parent
EVAL_SET_PATH = ROOT / "data" / "eval_set.jsonl"
RESULTS_DIR = ROOT / "eval_results"


def _cfg(name: str, prompt_variant: str, threshold: float | None = None) -> ExperimentConfig:
    return ExperimentConfig(name, {
        "model": settings.generation_model,
        "prompt_variant": prompt_variant,
        "confidence_threshold": threshold if threshold is not None else settings.confidence_threshold,
    })


PRESETS = {
    "v2": _cfg("v2", "v2_tuned"),
    "v1": _cfg("v1", "v1_naive"),
    "aggressive": _cfg("aggressive", "v1_naive", threshold=0.30),
}


def get_preset(name: str) -> ExperimentConfig:
    if name not in PRESETS:
        raise SystemExit(f"Unknown preset '{name}'. Options: {list(PRESETS)}")
    return PRESETS[name]


def load_cases(limit: int | None = None) -> list[dict]:
    cases = []
    with EVAL_SET_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases[:limit] if limit else cases


def run_preset(name: str, limit: int | None = None, use_judge: bool = True) -> dict:
    config = get_preset(name)
    p = config.params
    agent = DeflectionAgent(
        model=p["model"],
        prompt_variant=p["prompt_variant"],
        confidence_threshold=p["confidence_threshold"],
    )
    judge = Judge(model=settings.judge_model, rubric=DEFAULT_QUALITY_RUBRIC) if use_judge else None

    def run_case(case: dict) -> dict:
        result = agent.run(case["question"])
        grade = None
        if judge is not None:
            decision = "AUTO-RESOLVED" if not result.escalate else "ESCALATED to a human"
            grade = judge.grade(
                question=case["question"],
                answer=result.answer,
                context=scoring.context_text(result.retrieved),
                decision=decision,
            )
        return scoring.build_record(case, result, p["model"], grade)

    return run_experiment(
        config, load_cases(limit), run_case, scoring.aggregate, results_dir=RESULTS_DIR,
    )
