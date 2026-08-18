from __future__ import annotations

"""OpenAI adapter — isolates OpenAI SDK specifics (TTS, Whisper)."""


class OpenAIAdapter:
    """Adapter for OpenAI SDK specifics."""

    TTS_MODELS = ["tts-1", "tts-1-hd", "gpt-4o-mini-tts"]
    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    @staticmethod
    def tts_options(config: dict) -> dict:
        return {
            "model": config.get("tts_model", "gpt-4o-mini-tts"),
            "voice": config.get("voice", "alloy"),
            "response_format": "wav",
        }
