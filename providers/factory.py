from __future__ import annotations

from providers.streaming.deepgram import DeepgramProvider
from providers.streaming.assemblyai import AssemblyAIProvider
from providers.streaming.gladia import GladiaProvider
from providers.streaming.speechmatics import SpeechmaticsProvider
from providers.batch.elevenlabs import ElevenLabsProvider
from providers.batch.google_public import GooglePublicProvider

class ProviderFactory:

    _providers = {
        "deepgram": DeepgramProvider,
        "assemblyai": AssemblyAIProvider,
        "gladia": GladiaProvider,
        "speechmatics": SpeechmaticsProvider,
        "elevenlabs": ElevenLabsProvider,
        "google_public": GooglePublicProvider,
    }

    @classmethod
    def create(
        cls,
        name: str,
        config,
    ):

        try:

            return cls._providers[name.lower()](config)

        except KeyError:

            raise ValueError(f"Unknown provider: {name}")