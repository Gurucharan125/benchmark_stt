from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TranscriptChunk:

    text: str

    is_final: bool

    start: float

    end: float

    confidence: float | None = None


@dataclass(slots=True)
class Transcript:

    provider: str

    text: str

    chunks: list[TranscriptChunk]