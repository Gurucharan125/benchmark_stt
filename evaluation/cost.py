from __future__ import annotations

from dataclasses import dataclass


# Approximate pricing per minute of audio (USD)
PROVIDER_COSTS = {
    "deepgram": 0.0043,
    "assemblyai": 0.0050,
    "gladia": 0.0061,
    "speechmatics": 0.0070,
    "elevenlabs": 0.0050,
}


@dataclass(slots=True)
class CostEstimate:
    provider: str
    cost_per_minute: float
    audio_minutes: float
    total_cost: float


def estimate_cost(
    provider: str,
    audio_duration_seconds: float,
) -> CostEstimate:
    """Estimate the cost of transcribing audio with a given provider."""

    minutes = audio_duration_seconds / 60
    rate = PROVIDER_COSTS.get(provider.lower(), 0)

    return CostEstimate(
        provider=provider,
        cost_per_minute=rate,
        audio_minutes=round(minutes, 4),
        total_cost=round(rate * minutes, 6),
    )
