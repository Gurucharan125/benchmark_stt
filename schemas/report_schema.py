from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReportSchema:
    """Schema for validating report output structure."""
    provider: str
    transcript: str
    wer: float
    semantic_wer: float
    entity_accuracy: float
    ttfs_ms: float
    total_latency_ms: float
    success: bool
    error: str | None = None

    def validate(self) -> list[str]:
        errors = []
        if not self.provider:
            errors.append("Provider name is required")
        if self.wer < 0:
            errors.append("WER cannot be negative")
        return errors
