"""Adapter: wraps the production pipeline to satisfy agent-eval-kit's Agent
protocol. This is the only glue between the agent and the harness."""
from app.pipeline import SupportPipeline


class DeflectionAgent:
    """Satisfies agent_eval_kit.Agent: run(question) -> TicketResult."""

    def __init__(self, model=None, prompt_variant=None, confidence_threshold=None):
        self._pipeline = SupportPipeline(
            model=model,
            prompt_variant=prompt_variant,
            confidence_threshold=confidence_threshold,
        )

    def run(self, input: str):  # noqa: A002
        return self._pipeline.resolve(input)
