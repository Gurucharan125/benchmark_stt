from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ISTTProvider(ABC):

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
    ):
        ...