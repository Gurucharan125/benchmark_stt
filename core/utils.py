from __future__ import annotations

import json
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if needed."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_json(path: str | Path) -> dict | list:
    """Read and parse a JSON file."""
    with open(path, encoding="utf8") as f:
        return json.load(f)


def write_json(path: str | Path, data: dict | list, indent: int = 2):
    """Write data to a JSON file."""
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, indent=indent, default=str)


def format_ms(ms: float) -> str:
    """Format milliseconds for display."""
    if ms < 1000:
        return f"{ms:.1f}ms"
    return f"{ms / 1000:.2f}s"


def format_pct(value: float) -> str:
    """Format a percentage for display."""
    return f"{value:.1f}%"


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
