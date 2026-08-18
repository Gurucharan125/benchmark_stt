from __future__ import annotations

import asyncio
import logging
import sys

from core.config import cfg
from core.dataset import dataset_loader
from services.provider_service import provider_service
from services.report_service import report_service
from providers.factory import ProviderFactory
from pipelines.direct_pipeline import DirectPipeline

logger = logging.getLogger(__name__)


def benchmark_direct():
    """Benchmark all enabled providers using direct file transcription."""

    print("\n--- Benchmark Direct Providers ---")

    configs = provider_service.build_all_enabled()

    if not configs:
        print("No providers enabled. Set API keys in .env")
        return

    print(f"Providers: {[c.name for c in configs]}")

    dataset = dataset_loader.load(
        version=cfg.benchmark.get("dataset_version", "v1"),
        name=cfg.benchmark.get("dataset", "receptionist"),
    )

    print(f"Dataset: {dataset.name} ({len(dataset.samples)} samples)")

    all_results = []

    for config in configs:
        print(f"\nRunning: {config.name}...")
        provider = ProviderFactory.create(config.name, config)
        pipeline = DirectPipeline(provider)
        
        # We will loop here instead of pipeline.run_dataset to print immediately
        results = []
        for sample in dataset.samples:
            try:
                res = asyncio.run(pipeline.run_sample(sample))
                results.append(res)
                ent_score = res.entity_accuracy.score if hasattr(res.entity_accuracy, 'score') else res.entity_accuracy
                print(f"  Sample {sample.id}: WER={res.wer:.3f}  SemWER={res.semantic_wer:.3f}  EntityAcc={ent_score:.0f}%  TTFS={res.latency.ttfs_ms:.0f}ms  Total={res.latency.total_ms:.0f}ms  Success={res.success}")
                import time
                time.sleep(0.5)
            except Exception as e:
                print(f"  Sample {sample.id} failed: {e}")
                
        all_results.extend(results)

    paths = report_service.generate_all(all_results)
    print(f"\nReports saved to: {paths}")


def _run_twilio_server_pipeline(transport_class, pipeline_class, name):
    print(f"\n--- Benchmark {name} ---")
    
    from telephony.media_streams.websocket_server import MediaStreamServer
    from providers.factory import ProviderFactory
    
    configs = provider_service.build_all_enabled()
    if not configs:
        print("No providers enabled.")
        return
        
    dataset = dataset_loader.load(
        version=cfg.benchmark.get("dataset_version", "v1"),
        name=cfg.benchmark.get("dataset", "receptionist"),
    )
    if not dataset.samples:
        print("Dataset has no samples.")
        return
        
    config = configs[0]
    sample = dataset.samples[0]
    
    print(f"Waiting for Twilio stream to benchmark {config.name} with sample {sample.id}...")
    print("Run `python tests/mock_twilio_client.py` in another terminal to simulate Twilio.")
    
    server = MediaStreamServer(host="0.0.0.0", port=8765)
    transport = transport_class()
    
    async def on_connect(ws):
        await transport.connect()
        
    async def on_audio(pcm_16k, sid):
        await transport.stream(pcm_16k)
        
    async def on_disconnect(sid):
        await transport.close()
        
    server.on_connect(on_connect)
    server.on_audio(on_audio)
    server.on_disconnect(on_disconnect)
    
    async def run_server():
        server_task = asyncio.create_task(server.start())
        await transport.wait_done()
        server_task.cancel()
        
        provider = ProviderFactory.create(config.name, config)
        pipeline = pipeline_class(provider, transport)
        print("Stream received! Running pipeline evaluation...")
        result = await pipeline.run_from_buffer(sample)
        
        ent_score = result.entity_accuracy.score if hasattr(result.entity_accuracy, 'score') else result.entity_accuracy
        print(f"Result: WER={result.wer:.3f} SemWER={result.semantic_wer:.3f} EntityAcc={ent_score:.0f}% TTFS={result.latency.ttfs_ms:.0f}ms Total={result.latency.total_ms:.0f}ms Success={result.success}")
        
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nCancelled.")

def benchmark_twilio_media():
    """Benchmark providers via Twilio Media Streams."""
    from transports.twilio_media import TwilioMediaTransport
    from pipelines.twilio_pipeline import TwilioPipeline
    _run_twilio_server_pipeline(TwilioMediaTransport, TwilioPipeline, "Twilio Media Streams")

def benchmark_conversation_relay():
    """Benchmark providers via Twilio Conversation Relay."""
    from transports.conversation_relay import ConversationRelayTransport
    from pipelines.conversation_pipeline import ConversationPipeline
    _run_twilio_server_pipeline(ConversationRelayTransport, ConversationPipeline, "Conversation Relay")


def replay_calls():
    """Replay previously recorded call audio."""
    import glob

    print("\n--- Replay Previous Calls ---")
    replay_dir = cfg.root / "benchmark_audio" / "replay"
    wavs = list(replay_dir.glob("*.wav"))

    if not wavs:
        print(f"No recordings found in {replay_dir}")
        return

    print(f"Found {len(wavs)} recordings:")
    for i, w in enumerate(wavs):
        print(f"  {i + 1}. {w.name}")


# Hardcoded for the main benchmark suite
PROVIDERS = ["deepgram", "assemblyai", "elevenlabs", "google_public", "speechmatics", "gladia"]


def compare_runs():
    """Compare results from previous benchmark runs."""
    print("\n--- Compare Benchmark Runs ---")
    runs_dir = cfg.root / "storage" / "reports" / "runs"

    if not runs_dir.exists():
        print("No previous runs found.")
        return

    dates = sorted(d.name for d in runs_dir.iterdir() if d.is_dir())
    for d in dates:
        print(f"  {d}")


def generate_dashboard():
    """Generate the HTML dashboard."""
    print("\n--- Generate Dashboard ---")
    runs_dir = cfg.root / "storage" / "reports" / "runs"

    if not runs_dir.exists():
        print("No previous runs found.")
        return

    dates = sorted([d for d in runs_dir.iterdir() if d.is_dir()])
    if not dates:
        print("No previous runs found.")
        return

    latest_date_dir = dates[-1]
    runs = sorted([d for d in latest_date_dir.iterdir() if d.is_dir()])
    if not runs:
        print("No previous runs found.")
        return

    latest_run_dir = runs[-1]
    report_json = latest_run_dir / "report.json"

    if not report_json.exists():
        print(f"No report.json found in {latest_run_dir}")
        return

    import json
    from models.result import BenchmarkResult
    from models.transcript import Transcript
    from models.latency import Latency
    from evaluation.entities import EntityResult
    from dashboard import DashboardGenerator

    with open(report_json, encoding="utf8") as f:
        data = json.load(f)

    results = []
    for item in data:
        latency_dict = item.get("latency", {})
        latency = Latency(
            ttfs_ms=latency_dict.get("ttfs_ms", 0),
            total_ms=latency_dict.get("total_ms", 0),
        )

        entity_dict = item.get("entity_accuracy", {})
        if isinstance(entity_dict, dict):
            entity_acc = EntityResult(
                total=entity_dict.get("total", 0),
                matched=entity_dict.get("matched", 0),
                score=entity_dict.get("score", 0),
                missing=entity_dict.get("missing", []),
            )
        else:
            entity_acc = EntityResult(total=0, matched=0, score=float(entity_dict), missing=[])

        transcript = Transcript(provider=item["provider"], text=item.get("transcript", ""), chunks=[])

        results.append(BenchmarkResult(
            provider=item["provider"],
            transcript=transcript,
            latency=latency,
            wer=item.get("wer", 0),
            semantic_wer=item.get("semantic_wer", 0),
            entity_accuracy=entity_acc,
            success=item.get("success", False),
            error=item.get("error")
        ))

    dashboard = DashboardGenerator()
    path = dashboard.generate_dashboard(results)

    print(f"Dashboard generated at: {path}")
    print(f"Market comparison at: {path.parent / 'market_comparison.html'}")


def export_reports():
    """Export reports to charts/plots."""
    print("\n--- Export Reports ---")
    
    runs_dir = cfg.root / "storage" / "reports" / "runs"
    if not runs_dir.exists():
        print("No previous runs found.")
        return

    dates = sorted([d for d in runs_dir.iterdir() if d.is_dir()])
    if not dates:
        print("No previous runs found.")
        return

    latest_date_dir = dates[-1]
    runs = sorted([d for d in latest_date_dir.iterdir() if d.is_dir()])
    if not runs:
        print("No previous runs found.")
        return

    latest_run_dir = runs[-1]
    report_json = latest_run_dir / "report.json"

    if not report_json.exists():
        print(f"No report.json found in {latest_run_dir}")
        return

    import json
    from services.export_service import export_service
    
    with open(report_json, encoding="utf8") as f:
        data = json.load(f)

    # Export JSON
    json_path = export_service.export_json_summary(data)
    
    # Export CSV
    if not data:
        print("Report is empty.")
        return
        
    headers = list(data[0].keys())
    rows = []
    for item in data:
        row = []
        for key in headers:
            if isinstance(item.get(key), dict):
                row.append(json.dumps(item.get(key)))
            else:
                row.append(item.get(key))
        rows.append(row)
        
    csv_path = export_service.export_csv_summary(headers, rows)
    
    print(f"Exported JSON to: {json_path}")
    print(f"Exported CSV to: {csv_path}")


def diagnostics():
    """Run system diagnostics."""
    print("\n--- Diagnostics ---")
    print(f"Python: {sys.version}")
    print(f"Project root: {cfg.root}")
    print(f"Enabled providers: {cfg.enabled_providers}")

    try:
        cfg.validate()
        print("Configuration: VALID")
    except RuntimeError as e:
        print(f"Configuration: INVALID\n  {e}")


def settings():
    """Display current settings."""
    print("\n--- Settings ---")
    print(f"Dataset: {cfg.benchmark.get('dataset', 'receptionist')}")
    print(f"Voice: {cfg.benchmark.get('voice', 'alloy')}")
    print(f"Chunk MS: {cfg.benchmark.get('chunk_ms', 100)}")
    print(f"Enabled providers: {cfg.enabled_providers}")
