from __future__ import annotations

import json
import hashlib
import logging
from pathlib import Path

from core.config import cfg

logger = logging.getLogger(__name__)


class CacheService:
    """Manage cache for TTS audio, provider transcripts, and Twilio replays."""

    def __init__(self):
        self.root = cfg.root / "storage" / "cache"
        self.tts_dir = self.root / "tts"
        self.transcripts_dir = self.root / "transcripts"
        self.twilio_dir = self.root / "twilio"

        for d in (self.tts_dir, self.transcripts_dir, self.twilio_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _hash(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()[:24]

    # --- TTS cache ---

    def has_tts(self, text: str, voice: str, model: str) -> bool:
        key = f"{model}:{voice}:{text}"
        path = self.tts_dir / f"{self._hash(key)}.wav"
        return path.exists()

    def get_tts_path(self, text: str, voice: str, model: str) -> Path:
        key = f"{model}:{voice}:{text}"
        return self.tts_dir / f"{self._hash(key)}.wav"

    # --- Transcript cache ---

    def save_transcript(self, provider: str, sample_id: str, transcript: str):
        key = f"{provider}:{sample_id}"
        path = self.transcripts_dir / f"{self._hash(key)}.json"
        path.write_text(
            json.dumps({"provider": provider, "sample_id": sample_id, "transcript": transcript}),
            encoding="utf8",
        )
        logger.debug("Cached transcript: %s", path)

    def get_transcript(self, provider: str, sample_id: str) -> str | None:
        key = f"{provider}:{sample_id}"
        path = self.transcripts_dir / f"{self._hash(key)}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf8"))
        return data.get("transcript")

    # --- Twilio replay cache ---

    def save_twilio_audio(self, stream_sid: str, pcm: bytes) -> Path:
        path = self.twilio_dir / f"{stream_sid}.raw"
        path.write_bytes(pcm)
        logger.debug("Cached Twilio audio: %s", path)
        return path

    def get_twilio_audio(self, stream_sid: str) -> bytes | None:
        path = self.twilio_dir / f"{stream_sid}.raw"
        if not path.exists():
            return None
        return path.read_bytes()

    def clear(self, category: str | None = None):
        """Clear cache. If category is None, clear all."""
        dirs = {"tts": self.tts_dir, "transcripts": self.transcripts_dir, "twilio": self.twilio_dir}
        targets = [dirs[category]] if category and category in dirs else dirs.values()

        for d in targets:
            for f in d.iterdir():
                if f.is_file():
                    f.unlink()
            logger.info("Cleared cache: %s", d)


cache_service = CacheService()
