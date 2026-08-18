from __future__ import annotations

import logging

from core.config import cfg
from models.provider import ProviderConfig, ProviderType

logger = logging.getLogger(__name__)


class ProviderService:
    """Build ProviderConfig objects from YAML configs + .env API keys."""

    STREAMING_PROVIDERS = {"deepgram", "assemblyai", "gladia", "speechmatics"}
    BATCH_PROVIDERS = {"elevenlabs", "google_public"}

    def build_config(self, name: str) -> ProviderConfig:
        """Build a ProviderConfig for a given provider name."""

        yaml_cfg = cfg.yaml(name) if name != "google_public" else {}
        api_key = cfg.api_keys.get(name, "")

        if not api_key and name != "google_public":
            raise ValueError(f"No API key for provider: {name}")

        provider_type = (
            ProviderType.STREAMING
            if name in self.STREAMING_PROVIDERS
            else ProviderType.BATCH
        )

        return ProviderConfig(
            name=name,
            api_key=api_key,
            provider_type=provider_type,
            model=yaml_cfg.get("model", ""),
            sample_rate=yaml_cfg.get("sample_rate", 16000),
            channels=yaml_cfg.get("channels", 1),
            timeout=yaml_cfg.get("timeout", 30.0),
            retries=yaml_cfg.get("retries", 3),
            extra={
                k: v for k, v in yaml_cfg.items()
                if k not in ("name", "model", "sample_rate", "channels", "timeout", "retries")
            },
        )

    def build_all_enabled(self) -> list[ProviderConfig]:
        """Build configs for all providers that have API keys set."""
        configs = []
        for name in cfg.enabled_providers:
            try:
                configs.append(self.build_config(name))
                logger.info("Provider enabled: %s", name)
            except Exception as e:
                logger.warning("Skipping provider %s: %s", name, e)
        return configs


provider_service = ProviderService()
