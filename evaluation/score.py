from __future__ import annotations

from dataclasses import dataclass

from models.result import BenchmarkResult


@dataclass(slots=True)
class ScoreWeights:

    latency: float = 0.35

    entity: float = 0.30

    wer: float = 0.20

    reliability: float = 0.10

    cost: float = 0.05


class ProviderScorer:

    def __init__(
        self,
        weights: ScoreWeights | None = None,
    ):

        self.weights = weights or ScoreWeights()

    def latency_score(
        self,
        ms: float,
    ):

        return max(
            0,
            100 - ms / 10,
        )

    def wer_score(
        self,
        wer: float,
    ):

        return max(
            0,
            100 - wer * 100,
        )

    def reliability_score(
        self,
        success: bool,
    ):

        return 100 if success else 0

    def cost_score(
        self,
        cost: float = 0,
    ):

        if cost <= 0:
            return 100

        return max(
            0,
            100 - cost * 10,
        )

    def score(
        self,
        result: BenchmarkResult,
        cost: float = 0,
    ):

        latency = self.latency_score(
            result.latency.total_ms
        )

        wer = self.wer_score(
            result.wer
        )

        entity = result.entity_accuracy

        reliability = self.reliability_score(
            result.success
        )

        cost_score = self.cost_score(
            cost
        )

        final = (

            latency
            * self.weights.latency

            +

            entity
            * self.weights.entity

            +

            wer
            * self.weights.wer

            +

            reliability
            * self.weights.reliability

            +

            cost_score
            * self.weights.cost

        )

        return round(
            final,
            2,
        )


scorer = ProviderScorer()