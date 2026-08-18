from __future__ import annotations

"""Deepgram adapter — isolates SDK-specific details from the provider layer."""


class DeepgramAdapter:
    """Adapter for Deepgram SDK specifics.

    Use this to translate between the framework's internal
    audio format and Deepgram's expected input format."""

    ENCODING = "linear16"
    SAMPLE_RATE = 16000
    CHANNELS = 1

    @staticmethod
    def format_options(config: dict) -> dict:
        """Convert framework config to Deepgram SDK options."""
        return {
            "model": config.get("model", "nova-3"),
            "encoding": config.get("encoding", DeepgramAdapter.ENCODING),
            "sample_rate": config.get("sample_rate", DeepgramAdapter.SAMPLE_RATE),
            "channels": config.get("channels", DeepgramAdapter.CHANNELS),
            "smart_format": config.get("smart_format", True),
            "interim_results": config.get("interim_results", True),
        }
