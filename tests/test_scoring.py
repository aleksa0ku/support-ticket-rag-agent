"""Tests for the project-specific eval scoring (evals/scoring.py).

The generic harness mechanics (compare, gate, judge) are tested in
agent-eval-kit; these cover the deflection-agent metrics only. No API calls.
"""
from evals import scoring


def _rec(id, expected, predicted, sources=("d1",), expected_docs=("d1",),
         quality=1.0, passed=True, category="onboarding"):
    return {
        "id": id,
        "category": category,
        "question": "q",
        "expected_deflect": expected,
        "predicted_deflect": predicted,
        "decision_correct": expected == predicted,
        "sources": list(sources),
        "expected_doc_ids": list(expected_docs),
        "latency_ms": 1000.0,
        "agent_cost_usd": 0.01,
        "judge": {
            "faithfulness": 5, "helpfulness": 5, "safety": 5,
            "quality_score": quality, "passed": passed, "rationale": "",
        },
    }


def test_aggregate_confusion_and_rates():
    recs = [
        _rec("a", True, True),
        _rec("b", True, True),
        _rec("c", False, True),   # FP: auto-resolved something that should escalate
        _rec("d", False, False),  # TN
    ]
    m = scoring.aggregate(recs)
    assert m["confusion"] == {"tp": 2, "fp": 1, "tn": 1, "fn": 0}
    assert m["deflection_rate"] == 0.75
    assert abs(m["precision"] - 2 / 3) < 1e-9
    assert m["recall"] == 1.0


def test_citation_accuracy_only_correct_deflections():
    recs = [
        _rec("a", True, True, sources=["d1"], expected_docs=["d1"]),
        _rec("b", True, True, sources=["dX"], expected_docs=["d1"]),
    ]
    assert scoring.aggregate(recs)["citation_accuracy"] == 0.5


def test_judge_metrics_present():
    m = scoring.aggregate([_rec("a", True, True, quality=0.8)])
    assert m["avg_quality_score"] == 0.8
    assert m["quality_pass_rate"] == 1.0


def test_cost_estimate_uses_model_pricing():
    opus = scoring.estimate_cost_usd("claude-opus-4-8", 1_000_000, 0)
    haiku = scoring.estimate_cost_usd("claude-haiku-4-5", 1_000_000, 0)
    assert opus == 5.0 and haiku == 1.0
