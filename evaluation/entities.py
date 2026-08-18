from __future__ import annotations

from dataclasses import dataclass

from models.dataset import Entity


@dataclass(slots=True)
class EntityResult:

    total: int

    matched: int

    score: float

    missing: list[str]


def calculate_entity_accuracy(
    expected: list[Entity],
    transcript: str,
) -> EntityResult:

    if not expected:

        return EntityResult(
            total=0,
            matched=0,
            score=100.0,
            missing=[],
        )

    text = transcript.lower()

    matched = 0

    missing = []

    for entity in expected:

        value = entity.value.lower()

        if value in text:

            matched += 1

        else:

            missing.append(entity.value)

    score = (
        matched / len(expected)
    ) * 100

    return EntityResult(

        total=len(expected),

        matched=matched,

        score=score,

        missing=missing,

    )