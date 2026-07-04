"""Named experiment presets, referenced by the CLI scripts."""
from eval.config import ExperimentConfig

PRESETS = {
    # Production config: tuned prompt with explicit escalation policy.
    "v2": ExperimentConfig(name="v2", prompt_variant="v2_tuned", use_judge=True),
    # Naive baseline: no escalation guidance, no injection guardrails (but the
    # default confidence threshold still catches most risky cases downstream).
    "v1": ExperimentConfig(name="v1", prompt_variant="v1_naive", use_judge=True),
    # "Aggressive" config: a realistic bad change. Drops the escalation guidance
    # AND loosens the confidence threshold to chase a higher deflection rate —
    # defeating both safety layers, so it ships risky answers. Used to
    # demonstrate the regression gate catching a change before deploy.
    "aggressive": ExperimentConfig(
        name="aggressive", prompt_variant="v1_naive",
        confidence_threshold=0.30, use_judge=True,
    ),
}


def get_preset(name: str) -> ExperimentConfig:
    if name not in PRESETS:
        raise SystemExit(f"Unknown preset '{name}'. Options: {list(PRESETS)}")
    return PRESETS[name]
