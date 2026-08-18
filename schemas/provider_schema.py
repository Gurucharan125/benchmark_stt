from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProviderSchema:
    """Schema for validating provider configuration."""
    name: str
    api_key: str
    model: str
    sample_rate: int = 16000
    encoding: str = "linear16"
    channels: int = 1
    timeout: float = 30.0
    retries: int = 3

    def validate(self) -> list[str]:
        errors = []
        if not self.name:
            errors.append("Provider name is required")
        if not self.api_key:
            errors.append(f"API key is required for {self.name}")
        if self.sample_rate not in (8000, 16000, 44100, 48000):
            errors.append(f"Unusual sample rate: {self.sample_rate}")
        return errors
