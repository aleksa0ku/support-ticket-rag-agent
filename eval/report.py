"""Render an A/B comparison to human-readable markdown."""

_LABELS = {
    "escalation_accuracy": "Escalation-decision accuracy",
    "deflection_rate": "Deflection rate",
    "precision": "Precision (auto-resolved)",
    "recall": "Recall (resolvable)",
    "citation_accuracy": "Citation accuracy",
    "avg_quality_score": "Judge quality score (0-1)",
    "quality_pass_rate": "Judge pass rate",
    "blended_cost_usd": "Blended cost / ticket",
}


def _fmt(key: str, value) -> str:
    if value is None:
        return "—"
    if key == "blended_cost_usd":
        return f"${value:.2f}"
    if key == "avg_quality_score":
        return f"{value:.2f}"
    return f"{value * 100:.1f}%"


def render_markdown(cmp: dict) -> str:
    b_name = cmp["baseline_config"]["name"]
    c_name = cmp["candidate_config"]["name"]
    lines = [
        f"# Eval comparison: `{b_name}` → `{c_name}`",
        "",
        f"- Baseline: `{cmp['baseline_run']}` "
        f"(prompt `{cmp['baseline_config']['prompt_variant']}`, model `{cmp['baseline_config']['model']}`)",
        f"- Candidate: `{cmp['candidate_run']}` "
        f"(prompt `{cmp['candidate_config']['prompt_variant']}`, model `{cmp['candidate_config']['model']}`)",
        "",
        "## Metric deltas",
        "",
        f"| Metric | {b_name} | {c_name} | Δ |",
        "|---|---|---|---|",
    ]
    for d in cmp["metric_deltas"]:
        label = _LABELS.get(d["metric"], d["metric"])
        arrow = "▲" if (d["delta"] > 0) == d["higher_is_better"] else "▼"
        if abs(d["delta"]) < 1e-9:
            arrow = "—"
        delta_str = _fmt(d["metric"], abs(d["delta"])) if d["metric"] != "blended_cost_usd" \
            else f"${abs(d['delta']):.2f}"
        lines.append(
            f"| {label} | {_fmt(d['metric'], d['baseline'])} | "
            f"{_fmt(d['metric'], d['candidate'])} | {arrow} {delta_str} |"
        )

    lines += ["", f"## Regressions ({len(cmp['regressions'])})", ""]
    if cmp["regressions"]:
        for r in cmp["regressions"]:
            lines.append(f"- `{r['id']}` ({r['category']}): {r['question']}")
    else:
        lines.append("_None — no ticket that was decided correctly by the baseline regressed._")

    lines += ["", f"## Improvements ({len(cmp['improvements'])})", ""]
    if cmp["improvements"]:
        for imp in cmp["improvements"]:
            lines.append(f"- `{imp['id']}` ({imp['category']}): {imp['question']}")
    else:
        lines.append("_None._")

    return "\n".join(lines) + "\n"
