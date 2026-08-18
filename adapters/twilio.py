from __future__ import annotations

"""Twilio adapter — isolates Twilio SDK specifics."""


class TwilioAdapter:
    """Adapter for Twilio-specific configuration and API calls."""

    MEDIA_STREAM_SAMPLE_RATE = 8000
    MEDIA_STREAM_ENCODING = "audio/x-mulaw"
    MEDIA_STREAM_CHANNELS = 1

    @staticmethod
    def media_stream_config(config: dict) -> dict:
        return {
            "sample_rate": TwilioAdapter.MEDIA_STREAM_SAMPLE_RATE,
            "encoding": TwilioAdapter.MEDIA_STREAM_ENCODING,
            "channels": TwilioAdapter.MEDIA_STREAM_CHANNELS,
            "account_sid": config.get("twilio_sid", ""),
            "auth_token": config.get("twilio_token", ""),
        }
