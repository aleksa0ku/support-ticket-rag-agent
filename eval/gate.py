"""Regression gate: fail if a candidate run drops any tracked metric past tolerance."""
from eval.compare import HIGHER_IS_BETTER

# Absolute tolerances per metric. A candidate may drop a metric by at most this
# much before the gate fails. Cost is allowed to rise by a small amount.
DEFAULT_TOLERANCES = {
    "escalation_accuracy": 0.03,
    "precision": 0.03,
    "citation_accuracy": 0.02,
    "avg_quality_score": 0.03,
    "quality_pass_rate": 0.05,
}
# For cost (lower is better) this is the max allowed increase.
COST_TOLERANCE = {"blended_cost_usd": 0.50}


def check_gate(
    baseline: dict,
    candidate: dict,
    tolerances: dict | None = None,
) -> tuple[bool, list[dict]]:
    """Return (passed, violations). A violation means the candidate regressed
    a metric beyond its tolerance."""
    tolerances = tolerances or {**DEFAULT_TOLERANCES, **COST_TOLERANCE}
    b_metrics, c_metrics = baseline["metrics"], candidate["metrics"]

    violations = []
    for key, tol in tolerances.items():
        b, c = b_metrics.get(key), c_metrics.get(key)
        if b is None or c is None:
            continue
        delta = c - b
        higher_better = key in HIGHER_IS_BETTER
        # For higher-is-better, a drop is negative delta; regression if delta < -tol.
        # For lower-is-better (cost), a rise is positive delta; regression if delta > tol.
        regressed = (delta < -tol) if higher_better else (delta > tol)
        if regressed:
            violations.append({
                "metric": key,
                "baseline": b,
                "candidate": c,
                "delta": delta,
                "tolerance": tol,
                "higher_is_better": higher_better,
            })

    return (len(violations) == 0, violations)
