from __future__ import annotations

import asyncio
import logging

from core.config import cfg
from core.dataset import dataset_loader
from core.metrics import compute_metrics
from services.provider_service import provider_service
from services.report_service import report_service
from providers.factory import ProviderFactory
from pipelines.direct_pipeline import DirectPipeline
from evaluation.comparison import compare_providers, recommend

logger = logging.getLogger(__name__)


async def run_benchmark(
    providers: list[str] | None = None,
    dataset_name: str = "receptionist",
    dataset_version: str = "v1",
):
    """Run the full benchmark across all enabled providers."""

    # Discover providers
    configs = provider_service.build_all_enabled()
    if providers:
        configs = [c for c in configs if c.name in providers]

    if not configs:
        logger.error("No providers available")
        return

    # Load dataset
    dataset = dataset_loader.load(
        version=dataset_version,
        name=dataset_name,
    )
    logger.info("Dataset: %s v%s (%d samples)", dataset.name, dataset.version, len(dataset.samples))

    # Run each provider
    provider_results = {}

    for config in configs:
        logger.info("Benchmarking provider: %s", config.name)
        provider = ProviderFactory.create(config.name, config)

        pipeline = DirectPipeline(provider)
        results = await pipeline.run_dataset(dataset.samples)
        provider_results[config.name] = results

        metrics = compute_metrics(config.name, results)
        logger.info(
            "%s: score=%.2f wer=%.4f latency=%.0fms",
            config.name, metrics.score, metrics.wer, metrics.latency.mean_ms,
        )

    # Compare & rank
    all_results = []
    for results in provider_results.values():
        all_results.extend(results)

    comparisons = compare_providers(provider_results)
    winner = recommend(comparisons)
    logger.info("Recommended provider: %s", winner)

    # Generate reports
    report_service.generate_all(all_results)

    return provider_results
