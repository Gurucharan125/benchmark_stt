from __future__ import annotations

import logging
from pathlib import Path

from core.reporter import reporter
from models.result import BenchmarkResult

logger = logging.getLogger(__name__)


class ReportService:
    """Coordinate report generation across formats."""

    def generate_all(
        self,
        results: list[BenchmarkResult],
    ) -> dict[str, Path]:
        """Generate JSON, CSV, and Markdown reports. Returns paths."""

        paths = {}

        paths["json"] = reporter.save_json(results)
        logger.info("JSON report: %s", paths["json"])

        paths["csv"] = reporter.save_csv(results)
        logger.info("CSV report: %s", paths["csv"])

        paths["markdown"] = reporter.save_markdown(results)
        logger.info("Markdown report: %s", paths["markdown"])

        return paths


report_service = ReportService()
