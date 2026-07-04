import hashlib
from dataclasses import asdict, dataclass

from app.config import settings
from app.prompts import DEFAULT_VARIANT


@dataclass(frozen=True)
class ExperimentConfig:
    """A named, reproducible configuration of the agent under test."""
    name: str
    model: str = ""
    prompt_variant: str = DEFAULT_VARIANT
    confidence_threshold: float = 0.0
    use_judge: bool = True

    def resolved(self) -> "ExperimentConfig":
        """Fill in empty fields from the environment defaults."""
        return ExperimentConfig(
            name=self.name,
            model=self.model or settings.generation_model,
            prompt_variant=self.prompt_variant,
            confidence_threshold=self.confidence_threshold or settings.confidence_threshold,
            use_judge=self.use_judge,
        )

    @property
    def fingerprint(self) -> str:
        c = self.resolved()
        raw = f"{c.model}|{c.prompt_variant}|{c.confidence_threshold}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self.resolved()) | {"fingerprint": self.fingerprint}
