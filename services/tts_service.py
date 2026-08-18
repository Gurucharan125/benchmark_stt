from __future__ import annotations

import hashlib
from pathlib import Path

from openai import OpenAI

from core.config import cfg


class TTSService:

    def __init__(self):

        self.client = OpenAI(
            api_key=cfg.api_keys["openai"]
        )

        self.cache = (
            cfg.root
            / "storage"
            / "cache"
            / "tts"
        )

        self.output = (
            cfg.root
            / "benchmark_audio"
            / "generated"
        )

        self.cache.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.output.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _filename(
        self,
        text: str,
        voice: str,
        model: str,
    ) -> str:

        key = f"{model}:{voice}:{text}"

        return hashlib.sha256(
            key.encode()
        ).hexdigest()[:20]

    def generate(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "gpt-4o-mini-tts",
        overwrite: bool = False,
    ) -> Path:

        name = self._filename(
            text,
            voice,
            model,
        )

        path = self.cache / f"{name}.wav"

        if path.exists() and not overwrite:
            return path

        with self.client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text,
            response_format="wav",
        ) as response:

            response.stream_to_file(path)

        return path

    def benchmark_copy(
        self,
        audio: Path,
    ) -> Path:

        out = self.output / audio.name

        if not out.exists():

            out.write_bytes(
                audio.read_bytes()
            )

        return out


tts = TTSService()