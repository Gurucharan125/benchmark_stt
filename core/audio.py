from __future__ import annotations

import audioop
import wave
from pathlib import Path

from core.config import cfg


class AudioManager:

    def __init__(self):

        self.sample_rate = 16000

        self.channels = 1

        self.sample_width = 2

    def read_wav(
        self,
        path: str | Path,
    ):

        with wave.open(str(path), "rb") as wf:

            pcm = wf.readframes(
                wf.getnframes()
            )

            return {
                "pcm": pcm,
                "sample_rate": wf.getframerate(),
                "channels": wf.getnchannels(),
                "sample_width": wf.getsampwidth(),
                "frames": wf.getnframes(),
            }

    def duration(
        self,
        pcm: bytes,
    ):

        return len(pcm) / (
            self.sample_rate
            * self.sample_width
        )

    def pcm_chunks(
        self,
        pcm: bytes,
        chunk_ms: int = 100,
    ):

        bytes_per_second = (
            self.sample_rate
            * self.sample_width
            * self.channels
        )

        chunk_size = (
            bytes_per_second
            * chunk_ms
        ) // 1000

        for i in range(
            0,
            len(pcm),
            chunk_size,
        ):

            yield pcm[
                i:i + chunk_size
            ]

    def pcm_to_mulaw(
        self,
        pcm: bytes,
    ):

        return audioop.lin2ulaw(
            pcm,
            self.sample_width,
        )

    def mulaw_to_pcm(
        self,
        ulaw: bytes,
    ):

        return audioop.ulaw2lin(
            ulaw,
            self.sample_width,
        )

    def resample(
        self,
        pcm: bytes,
        source_rate: int,
        target_rate: int,
    ):

        if source_rate == target_rate:
            return pcm

        converted, _ = audioop.ratecv(
            pcm,
            self.sample_width,
            self.channels,
            source_rate,
            target_rate,
            None,
        )

        return converted

    def wav_bytes(
        self,
        path: str | Path,
    ):

        with open(path, "rb") as f:
            return f.read()

    def load(
        self,
        path: str | Path,
    ):

        return self.read_wav(path)["pcm"]

    def chunk_file(
        self,
        path: str | Path,
        chunk_ms=100,
    ):

        pcm = self.load(path)

        yield from self.pcm_chunks(
            pcm,
            chunk_ms=chunk_ms,
        )


audio = AudioManager()