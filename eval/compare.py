"""Diff two experiment runs: per-metric deltas and per-item flips."""

# Metrics where higher is better (for coloring / gate direction).
HIGHER_IS_BETTER = {
    "deflection_rate", "escalation_accuracy", "precision", "recall",
    "citation_accuracy", "avg_quality_score", "quality_pass_rate",
    "avg_faithfulness", "avg_helpfulness", "avg_safety",
}
# Metrics we track in the headline comparison table, in display order.
TRACKED = [
    "escalation_accuracy", "deflection_rate", "precision", "recall",
    "citation_accuracy", "avg_quality_score", "quality_pass_rate", "blended_cost_usd",
]


def compare(baseline: dict, candidate: dict) -> dict:
    b_metrics, c_metrics = baseline["metrics"], candidate["metrics"]

    metric_deltas = []
    for key in TRACKED:
        b, c = b_metrics.get(key), c_metrics.get(key)
        if b is None or c is None:
            continue
        metric_deltas.append({
            "metric": key,
            "baseline": b,
            "candidate": c,
            "delta": c - b,
            "higher_is_better": key in HIGHER_IS_BETTER,
        })

    # Per-item flips on the routing decision.
    b_items = {it["id"]: it for it in baseline["items"]}
    regressions, improvements = [], []
    for c_it in candidate["items"]:
        b_it = b_items.get(c_it["id"])
        if b_it is None:
            continue
        if b_it["decision_correct"] and not c_it["decision_correct"]:
            regressions.append(_flip(c_it, "decision"))
        elif not b_it["decision_correct"] and c_it["decision_correct"]:
            improvements.append(_flip(c_it, "decision"))

    return {
        "baseline_run": baseline["run_id"],
        "candidate_run": candidate["run_id"],
        "baseline_config": baseline["config"],
        "candidate_config": candidate["config"],
        "metric_deltas": metric_deltas,
        "regressions": regressions,
        "improvements": improvements,
    }


def _flip(item: dict, kind: str) -> dict:
    return {
        "id": item["id"],
        "category": item.get("category", ""),
        "question": item.get("question", ""),
        "kind": kind,
        "expected_deflect": item["expected_deflect"],
        "predicted_deflect": item["predicted_deflect"],
    }
