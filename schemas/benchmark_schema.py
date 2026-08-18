from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class BenchmarkSchema:
    """Schema for validating benchmark configuration."""
    dataset: str = "receptionist"
    version: str = "v1"
    voice: str = "alloy"
    tts_model: str = "gpt-4o-mini-tts"
    chunk_ms: int = 100
    parallel: bool = False
    retries: int = 3
    timeout: float = 30.0
    providers: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.dataset:
            errors.append("Dataset name is required")
        if self.chunk_ms < 10 or self.chunk_ms > 1000:
            errors.append(f"chunk_ms should be 10-1000, got {self.chunk_ms}")
        return errors
