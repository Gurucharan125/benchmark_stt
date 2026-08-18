from __future__ import annotations

import asyncio
import logging
import time

from models.dataset import Sample
from models.result import BenchmarkResult
from models.transcript import Transcript
from models.latency import Latency
from evaluation.wer import calculate_wer
from evaluation.semantic import calculate_semantic_wer
from evaluation.entities import calculate_entity_accuracy
from providers.base import STTProvider
from transports.replay import ReplayTransport
from telemetry.timer import Timer

logger = logging.getLogger(__name__)


class ReplayPipeline:
    """Replay previously recorded call audio through an STT provider."""

    def __init__(
        self,
        provider: STTProvider,
        chunk_ms: int = 100,
        realtime: bool = True,
    ):
        self.provider = provider
        self.chunk_ms = chunk_ms
        self.realtime = realtime

    async def run_sample(self, sample: Sample) -> BenchmarkResult:
        transport = ReplayTransport(sample.audio, chunk_ms=self.chunk_ms)
        timer = Timer()

        await transport.connect()
        await self.provider.connect()
        await self.provider.start()

        timer.start()

        start_time = time.perf_counter()
        for i, chunk in enumerate(transport.iter_chunks()):
            await self.provider.stream(chunk)
            if self.realtime:
                target_time = start_time + (i + 1) * (self.chunk_ms / 1000.0)
                sleep_duration = target_time - time.perf_counter()
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)

        await self.provider.finish()
        total_ms = timer.stop()

        await transport.close()
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

    async def run_dataset(self, samples: list[Sample]) -> list[BenchmarkResult]:
        results = []
        for sample in samples:
            logger.info("Replay pipeline: %s", sample.id)
            try:
                result = await self.run_sample(sample)
                results.append(result)
            except Exception as e:
                logger.error("Sample %s failed: %s", sample.id, e)
        return results
