from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator, Callable

from models.provider import (
    ProviderConfig,
    ProviderState,
)

from models.result import BenchmarkResult
from models.transcript import TranscriptChunk
from models.latency import Latency


class STTProvider(ABC):

    def __init__(self, config: ProviderConfig):

        self.config = config

        self.state = ProviderState()

        self._callback: Callable[[str, bool], None] | None = None
        self._text: str = ""
        self._chunks: list[TranscriptChunk] = []
        self._latency: Latency = Latency()

    @property
    def name(self) -> str:
        return self.config.name

    def set_callback(
        self,
        callback: Callable[[str, bool], None],
    ):
        self._callback = callback

    async def emit(
        self,
        text: str,
        final: bool,
    ):
        if self._callback:
            self._callback(text, final)

    @abstractmethod
    async def connect(self):
        ...

    @abstractmethod
    async def start(self):
        ...

    @abstractmethod
    async def stream(
        self,
        chunk: bytes,
    ):
        ...

    @abstractmethod
    async def finish(self):
        ...

    @abstractmethod
    async def close(self):
        ...

    @abstractmethod
    async def transcribe_file(
        self,
        audio: Path,
    ) -> BenchmarkResult:
        ...

    async def __aenter__(self):

        await self.connect()

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        await self.close()