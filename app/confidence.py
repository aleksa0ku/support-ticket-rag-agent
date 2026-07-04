from app.config import settings
from app.schemas import Decision, GeneratedAnswer, RetrievedChunk

MIN_RETRIEVAL_SIMILARITY = 0.35


def decide(
    generated: GeneratedAnswer,
    retrieved: list[RetrievedChunk],
    threshold: float | None = None,
) -> Decision:
    if threshold is None:
        threshold = settings.confidence_threshold
    top_similarity = max((c.similarity for c in retrieved), default=0.0)

    # Blend the model's self-reported confidence with how strong the retrieval match was,
    # so a confidently-worded answer grounded in weak retrieval still gets escalated.
    final_confidence = 0.6 * generated.confidence + 0.4 * max(top_similarity, 0.0)
    final_confidence = max(0.0, min(1.0, final_confidence))

    if generated.should_escalate:
        return Decision(final_confidence, True, generated.escalation_reason or "model flagged for escalation")
    if top_similarity < MIN_RETRIEVAL_SIMILARITY:
        return Decision(final_confidence, True, "no sufficiently relevant context retrieved")
    if final_confidence < threshold:
        return Decision(
            final_confidence,
            True,
            f"confidence {final_confidence:.2f} below threshold {threshold}",
        )
    return Decision(final_confidence, False, "")
