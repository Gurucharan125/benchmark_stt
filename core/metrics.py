from __future__ import annotations

from dataclasses import dataclass

from models.result import BenchmarkResult
from evaluation.wer import calculate_wer
from evaluation.semantic import calculate_semantic_wer
from evaluation.entities import calculate_entity_accuracy, EntityResult
from evaluation.latency import calculate_latency_stats, LatencyStats
from evaluation.reliability import calculate_reliability, ReliabilityStats
from evaluation.cost import estimate_cost, CostEstimate
from evaluation.score import scorer


@dataclass(slots=True)
class MetricsSummary:
    provider: str
    score: float
    wer: float
    semantic_wer: float
    entity_accuracy: float
    latency: LatencyStats
    reliability: ReliabilityStats
    cost: CostEstimate | None = None


def compute_metrics(
    provider: str,
    results: list[BenchmarkResult],
    audio_duration_seconds: float = 0,
) -> MetricsSummary:
    """Compute all evaluation metrics for a single provider's results."""

    if not results:
        return MetricsSummary(
            provider=provider,
            score=0,
            wer=0,
            semantic_wer=0,
            entity_accuracy=0,
            latency=LatencyStats(),
            reliability=ReliabilityStats(),
        )

    mean_wer = sum(r.wer for r in results) / len(results)
    mean_sem = sum(r.semantic_wer for r in results) / len(results)

    entity_scores = []
    for r in results:
        if hasattr(r.entity_accuracy, "score"):
            entity_scores.append(r.entity_accuracy.score)
        else:
            entity_scores.append(float(r.entity_accuracy))
    mean_entity = sum(entity_scores) / len(entity_scores) if entity_scores else 0

    scores = [scorer.score(r) for r in results]
    mean_score = sum(scores) / len(scores)

    cost = estimate_cost(provider, audio_duration_seconds) if audio_duration_seconds > 0 else None

    return MetricsSummary(
        provider=provider,
        score=round(mean_score, 2),
        wer=round(mean_wer, 4),
        semantic_wer=round(mean_sem, 4),
        entity_accuracy=round(mean_entity, 2),
        latency=calculate_latency_stats(results),
        reliability=calculate_reliability(results),
        cost=cost,
    )
