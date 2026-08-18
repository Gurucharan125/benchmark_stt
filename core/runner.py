from deepgram.listen.v1.requests import listen_v1results_channel_alternatives_item_words_item
from deepgram.listen.v1.requests import listen_v1results_channel_alternatives_item_words_item
from deepgram.listen.v1.requests import listen_v1results_channel_alternatives_item_words_item
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from core.audio import audio
from core.dataset import dataset_loader
from core.reporter import reporter
from evaluation.semantic import calculate_semantic_wer
from evaluation.wer import calculate_wer
from providers.factory import ProviderFactory

logger = logging.getLogger(__name__)


class BenchmarkRunner:

    def __init__(
        self,
        provider_name: str,
        provider_config,
    ):

        self.provider_name = provider_name

        self.provider = ProviderFactory.create(
            provider_name,
            provider_config,
        )

    async def benchmark_dataset(
        self,
        version: str = "v1",
        dataset: str = "receptionist",
    ):

        ds = dataset_loader.load(
            version=version,
            name=dataset,
        )

        results = []

        logger.info(
            "Loaded %d samples",
            len(ds.samples),
        )

        for sample in ds.samples:

            logger.info(
                "Running sample %s",
                sample.id,
            )

            result = await self.run_sample(
                sample
            )

            results.append(result)

        reporter.save_json(results)

        reporter.save_csv(results)

        reporter.save_markdown(results)

        return results

    async def run_sample(
        self,
        sample,
    ):

        logger.info(
            "Transcribing %s",
            sample.audio,
        )

        start = time.perf_counter()

        result = await self.provider.transcribe_file(
            Path(sample.audio)
        )

        elapsed = (
            time.perf_counter()
            - start
        ) * 1000

        result.latency.total_ms = elapsed

        result.wer = calculate_wer(
            sample.text,
            result.transcript.text,
        )

        result.semantic_wer = (
            calculate_semantic_wer(
                sample.text,
                result.transcript.text,
            )
        )
        
        from evaluation.entities import (
            calculate_entity_accuracy,
                )

        entity = calculate_entity_accuracy(

    sample.entities,

    result.transcript.text,

    )

        result.entity_accuracy = entity.score

        return result

    async def benchmark_stream(
        self,
        sample,
        chunk_ms: int = 100,
        realtime: bool = True,
    ):

        logger.info(
            "Streaming sample %s",
            sample.id,
        )

        await self.provider.connect()

        await self.provider.start()

        start = time.perf_counter()

        for chunk in audio.chunk_file(
            sample.audio,
            chunk_ms=chunk_ms,
        ):

            await self.provider.stream(
                chunk
            )

            if realtime:
                await asyncio.sleep(
                    chunk_ms / 1000
                )

        await self.provider.finish()

        elapsed = (
            time.perf_counter()
            - start
        ) * 1000

        logger.info(
            "Streaming completed in %.2f ms",
            elapsed,
        )

        await self.provider.close()

    async def benchmark_file(
        self,
        audio_file: str | Path,
    ):

        return await self.provider.transcribe_file(
            Path(audio_file)
        )

    async def close(self):

        await self.provider.close()

