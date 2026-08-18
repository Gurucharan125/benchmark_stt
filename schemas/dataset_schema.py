from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EntitySchema:
    label: str
    value: str


@dataclass(slots=True)
class SampleSchema:
    id: str
    text: str
    intent: str = ""
    entities: list[EntitySchema] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.id:
            errors.append("Sample ID is required")
        if not self.text:
            errors.append(f"Sample {self.id}: text is required")
        return errors


@dataclass(slots=True)
class DatasetSchema:
    """Schema for validating dataset JSON files."""
    name: str
    version: str
    samples: list[SampleSchema] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.samples:
            errors.append("Dataset must have at least one sample")
        for s in self.samples:
            errors.extend(s.validate())
        return errors
