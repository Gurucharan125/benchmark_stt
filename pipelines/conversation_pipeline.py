from __future__ import annotations

import asyncio
import logging

from models.dataset import Sample
from models.result import BenchmarkResult
from models.transcript import Transcript
from models.latency import Latency
from evaluation.wer import calculate_wer
from evaluation.semantic import calculate_semantic_wer
from evaluation.entities import calculate_entity_accuracy
from providers.base import STTProvider
from transports.conversation_relay import ConversationRelayTransport
from telemetry.timer import Timer

logger = logging.getLogger(__name__)


class ConversationPipeline:
    """Benchmark STT through Twilio Conversation Relay.

    Similar to TwilioPipeline but uses the managed
    Conversation Relay transport instead of raw Media Streams."""

    def __init__(
        self,
        provider: STTProvider,
        transport: ConversationRelayTransport | None = None,
    ):
        self.provider = provider
        self.transport = transport or ConversationRelayTransport()

    async def run_from_buffer(self, sample: Sample) -> BenchmarkResult:
        timer = Timer()

        await self.provider.connect()
        await self.provider.start()

        timer.start()

        for chunk in self.transport.iter_chunks():
            await self.provider.stream(chunk)

        await self.provider.finish()
        total_ms = timer.stop()

        await self.provider.close()

        transcript = Transcript(
            provider=self.provider.name,
            text=self.provider._text,
            chunks=list(self.provider._chunks),
        )

        latency = Latency(
            ttfs_ms=self.provider._latency.ttfs_ms,
            total_ms=total_ms,
        )

        wer = calculate_wer(sample.text, transcript.text)
        sem_wer = calculate_semantic_wer(sample.text, transcript.text)
        entity_result = calculate_entity_accuracy(sample.entities, transcript.text)

        return BenchmarkResult(
            provider=self.provider.name,
            transcript=transcript,
            latency=latency,
            wer=wer,
            semantic_wer=sem_wer,
            entity_accuracy=entity_result,
            success=True,
        )
