from eval.compare import compare
from eval.gate import check_gate
from eval.metrics import compute_metrics


def _item(id, expected, predicted, sources=("d1",), expected_docs=("d1",),
          quality=1.0, passed=True, latency=1000.0, cost=0.01, category="onboarding"):
    judge = {
        "faithfulness": 5, "helpfulness": 5, "safety": 5,
        "quality_score": quality, "passed": passed, "rationale": "",
    }
    return {
        "id": id,
        "category": category,
        "question": "q",
        "expected_deflect": expected,
        "predicted_deflect": predicted,
        "decision_correct": expected == predicted,
        "sources": list(sources),
        "expected_doc_ids": list(expected_docs),
        "latency_ms": latency,
        "agent_cost_usd": cost,
        "judge": judge,
    }


def _run(name, items):
    return {
        "run_id": f"{name}-run",
        "config": {"name": name, "prompt_variant": name, "model": "m"},
        "metrics": compute_metrics(items),
        "items": items,
    }


def test_metrics_confusion_and_rates():
    # 2 correct deflects, 1 wrong deflect (should have escalated), 1 correct escalate.
    items = [
        _item("a", True, True),
        _item("b", True, True),
        _item("c", False, True),   # FP
        _item("d", False, False),  # TN
    ]
    m = compute_metrics(items)
    assert m["confusion"] == {"tp": 2, "fp": 1, "tn": 1, "fn": 0}
    assert m["deflection_rate"] == 0.75
    assert m["escalation_accuracy"] == 0.75
    assert abs(m["precision"] - 2 / 3) < 1e-9
    assert m["recall"] == 1.0


def test_citation_accuracy_only_counts_correct_deflections():
    items = [
        _item("a", True, True, sources=["d1"], expected_docs=["d1"]),   # cited right
        _item("b", True, True, sources=["dX"], expected_docs=["d1"]),   # cited wrong
    ]
    m = compute_metrics(items)
    assert m["citation_accuracy"] == 0.5


def test_judge_metrics_present_when_judged():
    m = compute_metrics([_item("a", True, True, quality=0.8, passed=True)])
    assert m["judged_n"] == 1
    assert m["avg_quality_score"] == 0.8
    assert m["quality_pass_rate"] == 1.0


def test_compare_detects_flips():
    baseline = _run("v1", [_item("a", False, True), _item("b", True, True)])   # a wrong, b right
    candidate = _run("v2", [_item("a", False, False), _item("b", True, False)])  # a fixed, b broke
    cmp = compare(baseline, candidate)
    reg_ids = {r["id"] for r in cmp["regressions"]}
    imp_ids = {i["id"] for i in cmp["improvements"]}
    assert reg_ids == {"b"}
    assert imp_ids == {"a"}


def test_gate_fails_on_accuracy_drop():
    baseline = _run("v2", [_item(str(i), True, True) for i in range(10)])
    # Candidate gets 4 of 10 escalation decisions wrong → big accuracy drop.
    cand_items = [_item(str(i), True, True) for i in range(6)] + \
                 [_item(str(i), False, True) for i in range(6, 10)]
    candidate = _run("v3", cand_items)
    passed, violations = check_gate(baseline, candidate)
    assert passed is False
    assert any(v["metric"] == "escalation_accuracy" for v in violations)


def test_gate_passes_when_stable():
    items = [_item(str(i), True, True) for i in range(10)]
    passed, violations = check_gate(_run("a", items), _run("b", list(items)))
    assert passed is True
    assert violations == []


def test_gate_fails_on_safety_incident_even_within_tolerance():
    # Aggregate metrics identical, so no metric violation — but the candidate
    # auto-resolves a prompt-injection ticket that should have escalated.
    good = [_item(str(i), True, True) for i in range(10)]
    bad = [_item(str(i), True, True) for i in range(9)] + [
        _item("inj", expected=False, predicted=True, category="off_topic"),
    ]
    baseline = _run("v2", good + [_item("inj", expected=False, predicted=False, category="off_topic")])
    candidate = _run("aggressive", bad)
    passed, violations = check_gate(baseline, candidate)
    assert passed is False
    safety = [v for v in violations if v["type"] == "safety"]
    assert len(safety) == 1
    assert safety[0]["id"] == "inj"
