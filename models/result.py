from __future__ import annotations

from dataclasses import dataclass

from models.latency import Latency
from models.transcript import Transcript

from evaluation.entities import EntityResult
@dataclass(slots=True)
class BenchmarkResult:

    provider: str

    transcript: Transcript

    latency: Latency

    wer: float

    semantic_wer: float

    entity_accuracy: EntityResult

    success: bool

    error: str | None = None