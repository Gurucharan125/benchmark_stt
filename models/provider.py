from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderType(str, Enum):
    STREAMING = "streaming"
    BATCH = "batch"


class ProviderStatus(str, Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    READY = "ready"
    STREAMING = "streaming"
    FINISHED = "finished"
    ERROR = "error"
    CLOSED = "closed"


@dataclass(slots=True)
class ProviderConfig:
    name: str
    api_key: str
    provider_type: ProviderType
    model: str
    sample_rate: int = 16000
    channels: int = 1
    timeout: float = 30.0
    retries: int = 3
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderState:
    status: ProviderStatus = ProviderStatus.IDLE
    connected: bool = False
    streaming: bool = False
    last_error: str | None = None
