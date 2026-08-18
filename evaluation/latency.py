from __future__ import annotations

from dataclasses import dataclass

from models.result import BenchmarkResult


@dataclass(slots=True)
class LatencyStats:
    min_ms: float = 0
    max_ms: float = 0
    mean_ms: float = 0
    median_ms: float = 0
    p95_ms: float = 0
    p99_ms: float = 0
    ttfs_mean_ms: float = 0


def calculate_latency_stats(
    results: list[BenchmarkResult],
) -> LatencyStats:
    """Compute latency distribution from a set of benchmark results."""

    if not results:
        return LatencyStats()

    totals = sorted(r.latency.total_ms for r in results)
    ttfs_values = [r.latency.ttfs_ms for r in results if r.latency.ttfs_ms > 0]

    n = len(totals)

    return LatencyStats(
        min_ms=totals[0],
        max_ms=totals[-1],
        mean_ms=sum(totals) / n,
        median_ms=totals[n // 2],
        p95_ms=totals[int(n * 0.95)] if n > 1 else totals[0],
        p99_ms=totals[int(n * 0.99)] if n > 1 else totals[0],
        ttfs_mean_ms=(sum(ttfs_values) / len(ttfs_values)) if ttfs_values else 0,
    )
