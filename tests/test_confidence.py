from app.confidence import decide
from app.schemas import GeneratedAnswer, RetrievedChunk


def _answer(confidence=0.9, should_escalate=False, cited=("billing-plans",)):
    return GeneratedAnswer(
        answer="Here's how it works.",
        confidence=confidence,
        cited_doc_ids=list(cited),
        should_escalate=should_escalate,
        escalation_reason="",
    )


def _chunk(similarity=0.8, doc_id="billing-plans"):
    return RetrievedChunk(
        doc_id=doc_id, source_type="doc", title="Plans", text="...", similarity=similarity
    )


def test_high_confidence_high_similarity_deflects():
    decision = decide(_answer(confidence=0.95), [_chunk(similarity=0.85)])
    assert decision.escalate is False


def test_model_flagged_escalation_wins():
    decision = decide(_answer(confidence=0.95, should_escalate=True), [_chunk(similarity=0.9)])
    assert decision.escalate is True


def test_weak_retrieval_forces_escalation():
    decision = decide(_answer(confidence=0.9), [_chunk(similarity=0.1)])
    assert decision.escalate is True
    assert "context" in decision.reason


def test_low_blended_confidence_escalates():
    decision = decide(_answer(confidence=0.3), [_chunk(similarity=0.3)])
    assert decision.escalate is True


def test_no_retrieved_chunks_escalates():
    decision = decide(_answer(confidence=0.9), [])
    assert decision.escalate is True
