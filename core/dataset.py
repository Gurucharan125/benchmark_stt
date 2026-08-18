from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from models.dataset import (
    Dataset,
    Sample,
    Entity,
)

from services.tts_service import tts

from core.config import cfg


class DatasetLoader:

    def __init__(self):

        self.root = (
            cfg.root /
            "datasets"
        )

    def load(
        self,
        version: str,
        name: str,
        generate_audio: bool = True,
    ) -> Dataset:

        file = (
            self.root /
            version /
            f"{name}.json"
        )

        if not file.exists():
            raise FileNotFoundError(file)

        with open(
            file,
            encoding="utf8",
        ) as f:

            raw = json.load(f)

        samples = []

        for item in raw["samples"]:

            entities = [
                Entity(
                    label=e["label"],
                    value=e["value"],
                )
                for e in item.get(
                    "entities",
                    [],
                )
            ]

            sample = Sample(

                id=item["id"],

                text=item["text"],

                intent=item.get(
                    "intent",
                    "",
                ),

                entities=entities,

            )

            if generate_audio:

                audio = tts.generate(
                    sample.text
                )

                audio = tts.benchmark_copy(
                    audio
                )

                sample.audio = str(audio)

            samples.append(sample)

        return Dataset(

            name=name,

            version=version,

            samples=samples,

        )

    def iter_samples(
        self,
        dataset: Dataset,
    ) -> Iterator[Sample]:

        for sample in dataset.samples:
            yield sample


dataset_loader = DatasetLoader()