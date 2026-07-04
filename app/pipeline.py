import time

from app.confidence import decide
from app.generator import Generator
from app.retriever import Retriever
from app.schemas import TicketResult


class SupportPipeline:
    def __init__(self, top_k: int = 5):
        self._retriever = Retriever()
        self._generator = Generator()
        self._top_k = top_k

    def resolve(self, question: str) -> TicketResult:
        start = time.perf_counter()
        retrieved = self._retriever.retrieve(question, top_k=self._top_k)
        generated = self._generator.generate(question, retrieved)
        decision = decide(generated, retrieved)
        latency_ms = (time.perf_counter() - start) * 1000

        return TicketResult(
            question=question,
            answer=generated.answer,
            confidence=decision.final_confidence,
            escalate=decision.escalate,
            escalate_reason=decision.reason,
            sources=generated.cited_doc_ids,
            retrieved=retrieved,
            latency_ms=latency_ms,
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
        )
