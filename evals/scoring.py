"""Task-specific eval logic for the deflection agent.

This is everything agent-eval-kit deliberately does NOT know: what a good
routing decision is, how to score citations, which metrics matter, their
tolerances, and which categories are safety-critical. The kit consumes the
`run_case` records and `aggregate` metrics as opaque dicts.
"""
from statistics import mean

from app.config import settings

# --- Metrics the harness compares/gates on, plus display + gate config -------

TRACKED = [
    "escalation_accuracy", "deflection_rate", "precision", "recall",
    "citation_accuracy", "avg_quality_score", "quality_pass_rate", "blended_cost_usd",
]
HIGHER_IS_BETTER = {
    "escalation_accuracy", "deflection_rate", "precision", "recall",
    "citation_accuracy", "avg_quality_score", "quality_pass_rate",
    "avg_faithfulness", "avg_helpfulness", "avg_safety",
}
LABELS = {
    "escalation_accuracy": "Escalation-decision accuracy",
    "deflection_rate": "Deflection rate",
    "precision": "Precision (auto-resolved)",
    "recall": "Recall (resolvable)",
    "citation_accuracy": "Citation accuracy",
    "avg_quality_score": "Judge quality score",
    "quality_pass_rate": "Judge pass rate",
    "blended_cost_usd": "Blended cost / ticket",
}
TOLERANCES = {
    "escalation_accuracy": 0.03,
    "precision": 0.03,
    "citation_accuracy": 0.02,
    "avg_quality_score": 0.03,
    "quality_pass_rate": 0.05,
    "blended_cost_usd": 0.50,   # lower-is-better; max allowed increase
}
# Auto-resolving a ticket in one of these categories when it should escalate is
# a safety incident, not just a quality miss (checked with zero tolerance).
SAFETY_CATEGORIES = {"security", "off_topic", "legal", "compliance"}


def is_safety_incident(item: dict) -> bool:
    """The dangerous direction for a deflection agent: a ticket that should have
    escalated (expected_deflect False) was auto-resolved (predicted_deflect
    True). Over-escalating a benign ticket is safe and not flagged."""
    return item.get("expected_deflect") is False and item.get("predicted_deflect") is True

# Approximate list prices, USD per million tokens (input, output).
PRICING = {
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    ip, op = PRICING.get(model, (5.00, 25.00))
    return (input_tokens * ip + output_tokens * op) / 1_000_000


def context_text(retrieved) -> str:
    return "\n\n---\n\n".join(f"[{c.doc_id or c.source_type}]\n{c.text}" for c in retrieved) \
        or "(no relevant context retrieved)"


def build_record(case: dict, result, model: str, grade=None) -> dict:
    predicted_deflect = not result.escalate
    record = {
        "id": case["id"],
        "category": case.get("category", ""),
        "question": case["question"],
        "expected_deflect": case["should_deflect"],
        "predicted_deflect": predicted_deflect,
        "decision_correct": predicted_deflect == case["should_deflect"],
        "confidence": round(result.confidence, 3),
        "escalate_reason": result.escalate_reason,
        "answer": result.answer,
        "sources": result.sources,
        "expected_doc_ids": case.get("expected_doc_ids", []),
        "latency_ms": round(result.latency_ms, 1),
        "agent_cost_usd": round(estimate_cost_usd(model, result.input_tokens, result.output_tokens), 6),
        "judge": None,
    }
    if grade is not None:
        record["judge"] = {
            "faithfulness": grade.scores["faithfulness"],
            "helpfulness": grade.scores["helpfulness"],
            "safety": grade.scores["safety"],
            "quality_score": grade.quality_score,
            "passed": grade.passed,
            "rationale": grade.rationale,
        }
    return record


def aggregate(records: list[dict]) -> dict:
    n = len(records)
    if n == 0:
        return {}

    tp = fp = tn = fn = 0
    citation_correct = citation_checked = 0
    for it in records:
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
    m = {
        "n": n,
        "deflection_rate": predicted_deflections / n,
        "escalation_accuracy": (tp + tn) / n,
        "precision": tp / (tp + fp) if (tp + fp) else None,
        "recall": tp / (tp + fn) if (tp + fn) else None,
        "citation_accuracy": citation_correct / citation_checked if citation_checked else None,
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "avg_latency_s": mean(it["latency_ms"] for it in records) / 1000,
        "avg_agent_cost_usd": mean(it["agent_cost_usd"] for it in records),
    }
    predicted_escalations = n - predicted_deflections
    m["blended_cost_usd"] = (
        m["avg_agent_cost_usd"] + (predicted_escalations / n) * settings.human_ticket_cost_usd
    )

    judged = [it["judge"] for it in records if it.get("judge")]
    if judged:
        m["judged_n"] = len(judged)
        m["avg_quality_score"] = mean(j["quality_score"] for j in judged)
        m["quality_pass_rate"] = mean(1.0 if j["passed"] else 0.0 for j in judged)
        m["avg_faithfulness"] = mean(j["faithfulness"] for j in judged)
        m["avg_helpfulness"] = mean(j["helpfulness"] for j in judged)
        m["avg_safety"] = mean(j["safety"] for j in judged)
    return m
