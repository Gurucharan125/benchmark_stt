from __future__ import annotations

from dataclasses import dataclass

from models.result import BenchmarkResult


@dataclass(slots=True)
class ReliabilityStats:
    total: int = 0
    success: int = 0
    failure: int = 0
    success_rate: float = 0
    failure_rate: float = 0
    errors: list[str] | None = None


def calculate_reliability(
    results: list[BenchmarkResult],
) -> ReliabilityStats:
    """Compute success/failure rates from benchmark results."""

    if not results:
        return ReliabilityStats()

    total = len(results)
    success = sum(1 for r in results if r.success)
    failure = total - success
    errors = [r.error for r in results if r.error]

    return ReliabilityStats(
        total=total,
        success=success,
        failure=failure,
        success_rate=(success / total) * 100,
        failure_rate=(failure / total) * 100,
        errors=errors if errors else None,
    )
