from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = ROOT / "configs"
DATASET_DIR = ROOT / "datasets"
AUDIO_DIR = ROOT / "benchmark_audio"
CACHE_DIR = ROOT / "storage" / "cache"
REPORT_DIR = ROOT / "storage" / "reports"

load_dotenv(ROOT / ".env")


class Config:

    def __init__(self):

        self.root = ROOT

        self._cache: dict[str, Any] = {}

    def yaml(self, name: str) -> dict:

        if name in self._cache:
            return self._cache[name]

        path = CONFIG_DIR / f"{name}.yaml"

        if not path.exists():
            raise FileNotFoundError(path)

        with open(path, "r", encoding="utf8") as f:
            cfg = yaml.safe_load(f) or {}

        self._cache[name] = cfg

        return cfg

    def env(self, key: str, default=None):

        return os.getenv(key, default)

    @property
    def benchmark(self):

        return self.yaml("benchmark")

    @property
    def deepgram(self):

        return self.yaml("deepgram")

    @property
    def assemblyai(self):

        return self.yaml("assemblyai")

    @property
    def gladia(self):

        return self.yaml("gladia")

    @property
    def speechmatics(self):

        return self.yaml("speechmatics")

    @property
    def elevenlabs(self):

        return self.yaml("elevenlabs")

    @property
    def twilio(self):

        return self.yaml("twilio")

    @property
    def api_keys(self):

        return {

            "deepgram":
                self.env("DEEPGRAM_API_KEY"),

            "assemblyai":
                self.env("ASSEMBLYAI_API_KEY"),

            "gladia":
                self.env("GLADIA_API_KEY"),

            "speechmatics":
                self.env("SPEECHMATICS_API_KEY"),

            "elevenlabs":
                self.env("ELEVENLABS_API_KEY"),

            "openai":
                self.env("OPENAI_API_KEY"),

            "twilio_sid":
                self.env("TWILIO_ACCOUNT_SID"),

            "twilio_token":
                self.env("TWILIO_AUTH_TOKEN"),

        }

    @property
    def enabled_providers(self):

        enabled = []

        for provider in [
            "deepgram",
            "assemblyai",
            "elevenlabs",
            "speechmatics",
            "gladia",
        ]:

            if self.api_keys.get(provider):
                enabled.append(provider)

        enabled.append("google_public")
        return enabled

    def validate(self):

        missing = []

        if not self.api_keys["openai"]:
            missing.append("OPENAI_API_KEY")

        if not self.enabled_providers:
            missing.append(
                "No STT provider API keys configured."
            )

        if missing:
            raise RuntimeError(
                "\n".join(missing)
            )


cfg = Config()