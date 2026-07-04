import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    generation_model: str
    judge_model: str
    embedding_model: str
    chroma_dir: str
    confidence_threshold: float
    human_ticket_cost_usd: float


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        generation_model=os.environ.get("GENERATION_MODEL", "claude-opus-4-8"),
        judge_model=os.environ.get("JUDGE_MODEL", "claude-haiku-4-5"),
        embedding_model=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        chroma_dir=os.environ.get("CHROMA_DIR", "./chroma_db"),
        confidence_threshold=float(os.environ.get("CONFIDENCE_THRESHOLD", "0.72")),
        human_ticket_cost_usd=float(os.environ.get("HUMAN_TICKET_COST_USD", "8.0")),
    )


settings = load_settings()
