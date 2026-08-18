from __future__ import annotations

from dataclasses import dataclass, field

from models.result import BenchmarkResult
from evaluation.latency import calculate_latency_stats, LatencyStats
from evaluation.reliability import calculate_reliability, ReliabilityStats
from evaluation.score import scorer


@dataclass(slots=True)
class ProviderComparison:
    provider: str
    score: float
    latency: LatencyStats
    reliability: ReliabilityStats
    mean_wer: float
    mean_entity_accuracy: float


@dataclass(slots=True)
class TwilioOverhead:
    provider: str
    direct_latency_ms: float
    twilio_latency_ms: float
    overhead_ms: float
    overhead_pct: float


def compare_providers(
    provider_results: dict[str, list[BenchmarkResult]],
) -> list[ProviderComparison]:
    """Compare multiple providers side-by-side."""

    comparisons = []

    for provider, results in provider_results.items():
        if not results:
            continue

        scores = [scorer.score(r) for r in results]
        wer_values = [r.wer for r in results]
        entity_values = [
            r.entity_accuracy.score
            if hasattr(r.entity_accuracy, "score")
            else r.entity_accuracy
            for r in results
        ]

        comparisons.append(
            ProviderComparison(
                provider=provider,
                score=sum(scores) / len(scores),
                latency=calculate_latency_stats(results),
                reliability=calculate_reliability(results),
                mean_wer=sum(wer_values) / len(wer_values),
                mean_entity_accuracy=sum(entity_values) / len(entity_values),
            )
        )

    comparisons.sort(key=lambda c: c.score, reverse=True)
    return comparisons


def compute_twilio_overhead(
    direct_results: dict[str, list[BenchmarkResult]],
    twilio_results: dict[str, list[BenchmarkResult]],
) -> list[TwilioOverhead]:
    """Compute Twilio overhead = Twilio Pipeline - Direct Pipeline."""

    overheads = []

    for provider in direct_results:
        if provider not in twilio_results:
            continue

        direct = direct_results[provider]
        twilio = twilio_results[provider]

        if not direct or not twilio:
            continue

        direct_mean = sum(r.latency.total_ms for r in direct) / len(direct)
        twilio_mean = sum(r.latency.total_ms for r in twilio) / len(twilio)
        overhead = twilio_mean - direct_mean

        overheads.append(
            TwilioOverhead(
                provider=provider,
                direct_latency_ms=round(direct_mean, 2),
                twilio_latency_ms=round(twilio_mean, 2),
                overhead_ms=round(overhead, 2),
                overhead_pct=round((overhead / direct_mean) * 100, 2) if direct_mean > 0 else 0,
            )
        )

    return overheads


def recommend(
    comparisons: list[ProviderComparison],
) -> str:
    """Return the name of the recommended provider based on composite score."""
    if not comparisons:
        return "No providers benchmarked"
    return comparisons[0].provider
