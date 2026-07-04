"""Run the eval set under an ExperimentConfig and persist a result file."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.judge import Judge
from app.pipeline import SupportPipeline
from eval.config import ExperimentConfig
from eval.metrics import compute_metrics, estimate_cost_usd

ROOT = Path(__file__).resolve().parent.parent
EVAL_SET_PATH = ROOT / "data" / "eval_set.jsonl"
RESULTS_DIR = ROOT / "eval_results"


def load_eval_set(limit: int | None = None) -> list[dict]:
    items = []
    with EVAL_SET_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items[:limit] if limit else items


def run_experiment(
    config: ExperimentConfig,
    limit: int | None = None,
    progress: bool = True,
) -> dict:
    config = config.resolved()
    eval_items = load_eval_set(limit)
    pipeline = SupportPipeline(
        model=config.model,
        prompt_variant=config.prompt_variant,
        confidence_threshold=config.confidence_threshold,
    )
    judge = Judge() if config.use_judge else None

    item_results = []
    for i, item in enumerate(eval_items, 1):
        result = pipeline.resolve(item["question"])
        predicted_deflect = not result.escalate
        agent_cost = estimate_cost_usd(config.model, result.input_tokens, result.output_tokens)

        record = {
            "id": item["id"],
            "question": item["question"],
            "category": item.get("category", ""),
            "expected_deflect": item["should_deflect"],
            "predicted_deflect": predicted_deflect,
            "decision_correct": predicted_deflect == item["should_deflect"],
            "confidence": round(result.confidence, 3),
            "escalate_reason": result.escalate_reason,
            "answer": result.answer,
            "sources": result.sources,
            "expected_doc_ids": item.get("expected_doc_ids", []),
            "latency_ms": round(result.latency_ms, 1),
            "agent_cost_usd": round(agent_cost, 6),
            "judge": None,
        }

        if judge is not None:
            grade = judge.grade(item["question"], result.answer, result.retrieved, result.escalate)
            record["judge"] = {
                "faithfulness": grade.faithfulness,
                "helpfulness": grade.helpfulness,
                "safety": grade.safety,
                "quality_score": grade.quality_score,
                "passed": grade.passed,
                "rationale": grade.rationale,
            }

        item_results.append(record)
        if progress:
            q = "quality " + format(record["judge"]["quality_score"], ".2f") if record["judge"] else ""
            print(f"[{i}/{len(eval_items)}] {item['id']}: "
                  f"{'DEFLECT' if predicted_deflect else 'ESCALATE'} "
                  f"({'ok' if record['decision_correct'] else 'WRONG'}) {q}")

    metrics = compute_metrics(item_results)
    run_id = f"{config.name}-{config.fingerprint}-{int(time.time())}"
    run = {
        "run_id": run_id,
        "config": config.to_dict(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "items": item_results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{run_id}.json"
    out_path.write_text(json.dumps(run, indent=2))
    run["_path"] = str(out_path)
    return run
