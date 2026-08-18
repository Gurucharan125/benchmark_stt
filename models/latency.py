from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Latency:

    connect_ms: float = 0

    first_partial_ms: float = 0

    ttfs_ms: float = 0

    final_ms: float = 0

    total_ms: float = 0