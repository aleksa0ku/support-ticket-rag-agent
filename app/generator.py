import anthropic

from app.config import settings
from app.prompts import get_prompt
from app.schemas import GeneratedAnswer, RetrievedChunk

ANSWER_TOOL = {
    "name": "submit_answer",
    "description": "Submit the drafted answer to the support ticket.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "answer": {"type": "string", "description": "The reply to send to the customer."},
            "confidence": {
                "type": "number",
                "description": (
                    "0-1 confidence that this answer alone fully resolves the ticket "
                    "with no human follow-up needed."
                ),
            },
            "cited_doc_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "doc_id values of context chunks actually used to ground the answer.",
            },
            "should_escalate": {
                "type": "boolean",
                "description": "True if a human should still handle or verify this ticket.",
            },
            "escalation_reason": {
                "type": "string",
                "description": "Short reason for escalation, empty string if should_escalate is false.",
            },
        },
        "required": ["answer", "confidence", "cited_doc_ids", "should_escalate", "escalation_reason"],
    },
}


def _sanitize_answer(answer: str) -> str:
    # Guards against rare cases where the model bleeds tool-call-formatting
    # artifacts (e.g. "</answer>", "<parameter ...>") into the answer string itself.
    for marker in ("</answer>", "<parameter"):
        index = answer.find(marker)
        if index != -1:
            answer = answer[:index].rstrip()
    return answer


class Generator:
    def __init__(self, model: str | None = None, prompt_variant: str | None = None):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = model or settings.generation_model
        self._system_prompt = get_prompt(prompt_variant)

    def generate(self, question: str, context_chunks: list[RetrievedChunk]) -> GeneratedAnswer:
        context_block = "\n\n---\n\n".join(
            f"[{c.doc_id or c.source_type} | similarity={c.similarity:.2f}]\n{c.text}"
            for c in context_chunks
        ) or "(no relevant context retrieved)"

        message = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=self._system_prompt,
            tools=[ANSWER_TOOL],
            tool_choice={"type": "tool", "name": "submit_answer"},
            messages=[{
                "role": "user",
                "content": f"Customer question:\n{question}\n\nRetrieved context:\n{context_block}",
            }],
        )

        tool_use = next(b for b in message.content if b.type == "tool_use")
        data = tool_use.input

        return GeneratedAnswer(
            answer=_sanitize_answer(data["answer"]),
            confidence=float(data["confidence"]),
            cited_doc_ids=list(data.get("cited_doc_ids", [])),
            should_escalate=bool(data["should_escalate"]),
            escalation_reason=data.get("escalation_reason", ""),
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
