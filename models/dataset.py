from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Entity:

    label: str

    value: str


@dataclass(slots=True)
class Sample:

    id: str

    text: str

    intent: str

    entities: list[Entity] = field(default_factory=list)

    audio: str | None = None


@dataclass(slots=True)
class Dataset:

    name: str

    version: str

    samples: list[Sample]