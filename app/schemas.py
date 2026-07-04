from dataclasses import dataclass, field
from typing import Literal


@dataclass
class RetrievedChunk:
    doc_id: str
    source_type: Literal["doc", "ticket"]
    title: str
    text: str
    similarity: float


@dataclass
class GeneratedAnswer:
    answer: str
    confidence: float
    cited_doc_ids: list[str]
    should_escalate: bool
    escalation_reason: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class Decision:
    final_confidence: float
    escalate: bool
    reason: str


@dataclass
class JudgeResult:
    faithfulness: int
    helpfulness: int
    safety: int
    quality_score: float
    passed: bool
    rationale: str


@dataclass
class TicketResult:
    question: str
    answer: str
    confidence: float
    escalate: bool
    escalate_reason: str
    sources: list[str]
    retrieved: list[RetrievedChunk] = field(default_factory=list)
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
