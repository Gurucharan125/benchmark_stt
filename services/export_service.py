from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from core.config import cfg

logger = logging.getLogger(__name__)


class ExportService:
    """Export benchmark results to charts, plots, and summary files."""

    def __init__(self):
        self.export_root = cfg.root / "exports"
        self.charts_dir = self.export_root / "charts"
        self.plots_dir = self.export_root / "plots"
        self.ppt_dir = self.export_root / "ppt"

        for d in (self.charts_dir, self.plots_dir, self.ppt_dir):
            d.mkdir(parents=True, exist_ok=True)

    def export_json_summary(
        self,
        data: list[dict],
        filename: str = "summary.json",
    ) -> Path:
        path = self.export_root / filename
        with open(path, "w", encoding="utf8") as f:
            json.dump(data, f, indent=2)
        logger.info("Exported JSON summary: %s", path)
        return path

    def export_csv_summary(
        self,
        headers: list[str],
        rows: list[list],
        filename: str = "summary.csv",
    ) -> Path:
        path = self.export_root / filename
        with open(path, "w", newline="", encoding="utf8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        logger.info("Exported CSV summary: %s", path)
        return path


export_service = ExportService()
