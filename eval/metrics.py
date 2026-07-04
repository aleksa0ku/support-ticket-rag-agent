"""Aggregate metric computation over per-item eval results."""
from statistics import mean

from app.config import settings

# Approximate list prices, USD per million tokens (input, output).
# Verify against https://platform.claude.com/docs/en/pricing before real budgeting.
PRICING = {
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = PRICING.get(model, (5.00, 25.00))
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def compute_metrics(items: list[dict]) -> dict:
    """Compute aggregate metrics from a list of per-item result dicts.

    Deterministic metrics come from the ground-truth labels; the judge-*
    metrics come from the LLM-as-judge grades (present only when judged).
    """
    n = len(items)
    if n == 0:
        return {}

    tp = fp = tn = fn = 0
    citation_correct = citation_checked = 0
    for it in items:
        pred, exp = it["predicted_deflect"], it["expected_deflect"]
        if pred and exp:
            tp += 1
        elif pred and not exp:
            fp += 1
        elif not pred and not exp:
            tn += 1
        else:
            fn += 1
        if pred and exp and it.get("expected_doc_ids"):
            citation_checked += 1
            if set(it.get("sources", [])) & set(it["expected_doc_ids"]):
                citation_correct += 1

    predicted_deflections = tp + fp
    metrics = {
        "n": n,
        "deflection_rate": predicted_deflections / n,
        "escalation_accuracy": (tp + tn) / n,
        "precision": tp / (tp + fp) if (tp + fp) else None,
        "recall": tp / (tp + fn) if (tp + fn) else None,
        "citation_accuracy": citation_correct / citation_checked if citation_checked else None,
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "avg_latency_s": mean(it["latency_ms"] for it in items) / 1000,
        "avg_agent_cost_usd": mean(it["agent_cost_usd"] for it in items),
    }

    predicted_escalations = n - predicted_deflections
    metrics["blended_cost_usd"] = (
        metrics["avg_agent_cost_usd"]
        + (predicted_escalations / n) * settings.human_ticket_cost_usd
    )

    judged = [it["judge"] for it in items if it.get("judge")]
    if judged:
        metrics["judged_n"] = len(judged)
        metrics["avg_quality_score"] = mean(j["quality_score"] for j in judged)
        metrics["quality_pass_rate"] = mean(1.0 if j["passed"] else 0.0 for j in judged)
        metrics["avg_faithfulness"] = mean(j["faithfulness"] for j in judged)
        metrics["avg_helpfulness"] = mean(j["helpfulness"] for j in judged)
        metrics["avg_safety"] = mean(j["safety"] for j in judged)

    return metrics
