from __future__ import annotations

import csv
import json
import dataclasses
from datetime import datetime
from pathlib import Path

from models.result import BenchmarkResult
from core.config import cfg

from evaluation.ranking import ranking
class Reporter:

    def __init__(self):

        self.root = (
            cfg.root /
            "storage" /
            "reports"
        )

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _run_folder(self):

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        folder = (
            self.root /
            "runs" /
            today /
            datetime.now().strftime(
                "run_%H%M%S"
            )
        )

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        return folder

    def save_json(
        self,
        results: list[BenchmarkResult],
    ):

        folder = self._run_folder()

        out = folder / "report.json"

        payload = []

        for r in results:

            payload.append({
                "provider": r.provider,
                "transcript": r.transcript.text,
                "wer": r.wer,
                "semantic_wer": r.semantic_wer,
                "entity_accuracy": dataclasses.asdict(r.entity_accuracy) if hasattr(r.entity_accuracy, "__dataclass_fields__") else r.entity_accuracy,
                "latency": dataclasses.asdict(r.latency),
                "success": r.success,
                "error": r.error,
            })

        with open(
            out,
            "w",
            encoding="utf8",
        ) as f:

            json.dump(
                payload,
                f,
                indent=4,
            )

        return out

    def save_csv(
        self,
        results: list[BenchmarkResult],
    ):

        folder = self._run_folder()

        out = folder / "report.csv"

        with open(
            out,
            "w",
            newline="",
            encoding="utf8",
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "Provider",
                "WER",
                "SemanticWER",
                "EntityAccuracy",
                "TTFS",
                "Latency",
                "Success",
            ])

            for r in results:

                writer.writerow([
                    r.provider,
                    r.wer,
                    r.semantic_wer,
                    r.entity_accuracy,
                    r.latency.ttfs_ms,
                    r.latency.total_ms,
                    r.success,
                ])

        return out

    def save_markdown(
        self,
        results: list[BenchmarkResult],
    ):

        folder = self._run_folder()

        out = folder / "summary.md"

        lines = []

        lines.append("# Benchmark Summary\n")

        for r in results:

            lines.append(
                f"## {r.provider}"
            )

            lines.append(
                f"- Transcript: {r.transcript.text}"
            )

            lines.append(
                f"- WER: {r.wer:.3f}"
            )

            lines.append(
                f"- TTFS: {r.latency.ttfs_ms:.1f} ms"
            )

            lines.append(
                f"- Total: {r.latency.total_ms:.1f} ms"
            )

            lines.append("")

        out.write_text(
            "\n".join(lines),
            encoding="utf8",
        )

        return out


reporter = Reporter()