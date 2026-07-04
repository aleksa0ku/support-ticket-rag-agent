from fastapi import FastAPI
from pydantic import BaseModel

from app.pipeline import SupportPipeline

app = FastAPI(
    title="Cloudbox Support Deflection Agent",
    description="RAG agent that drafts or auto-resolves support tickets, escalating low-confidence cases.",
)

_pipeline: SupportPipeline | None = None


def get_pipeline() -> SupportPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = SupportPipeline()
    return _pipeline


class TicketRequest(BaseModel):
    question: str


class TicketResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    escalate: bool
    escalate_reason: str
    sources: list[str]
    latency_ms: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets/resolve", response_model=TicketResponse)
def resolve_ticket(request: TicketRequest):
    result = get_pipeline().resolve(request.question)
    return TicketResponse(
        question=result.question,
        answer=result.answer,
        confidence=result.confidence,
        escalate=result.escalate,
        escalate_reason=result.escalate_reason,
        sources=result.sources,
        latency_ms=result.latency_ms,
    )
