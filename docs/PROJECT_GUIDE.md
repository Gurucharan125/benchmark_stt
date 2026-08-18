# AI Receptionist Evaluation Framework — Project Guide

> This document is the single source of truth for any agent working on this codebase.
> Read it fully before making changes.

## 1. What This Project Does

This is a **benchmarking framework** that evaluates multiple **Speech-to-Text (STT) providers** for use in an AI Receptionist voice agent. It answers the question: *"Which STT provider gives us the best transcription quality, lowest latency, and highest reliability — both in direct API mode and when audio arrives through Twilio?"*

### The core workflow

```
Dataset (JSON)                    OpenAI TTS
    |                                 |
    v                                 v
 Sample text  ------------>  Generated WAV audio
                                      |
                    +-----------------+------------------+
                    v                 v                  v
             Direct Transport   Twilio Media       Replay Transport
                    |           Streams Transport        |
                    v                 v                  v
              STT Provider      STT Provider       STT Provider
             (Deepgram, etc)   (Deepgram, etc)    (Deepgram, etc)
                    |                 |                  |
                    v                 v                  v
               Transcript        Transcript          Transcript
                    |                 |                  |
                    +-----------------+------------------+
                                      v
                              Evaluation Engine
                         (WER, Entity Accuracy, Latency)
                                      |
                                      v
                              Scoring & Ranking
                                      |
                                      v
                              Reports (JSON, CSV, MD, HTML)
```

### Key measurements

| Metric | What it measures |
|--------|-----------------|
| **WER** | Word Error Rate - raw transcription accuracy |
| **Semantic WER** | Case-insensitive WER for meaning comparison |
| **Entity Accuracy** | Did the STT correctly capture names, dates, phone numbers? |
| **TTFS** | Time To First Speech - latency until first partial transcript |
| **Total Latency** | End-to-end time for full transcription |
| **Twilio Overhead** | Twilio Pipeline latency - Direct Pipeline latency |
| **Reliability** | Success/failure rate across samples |
| **Cost** | Per-provider pricing comparison |

## 2. Architecture Layers

```
+--------------------------------------------------+
|                    CLI (cli/)                     |  User interface
+--------------------------------------------------+
|                 Pipelines (pipelines/)            |  Orchestration
+--------------------------------------------------+
|  Transports (transports/)  |  Providers (providers/)  |  I/O
+--------------------------------------------------+
|                 Services (services/)              |  Business logic
+--------------------------------------------------+
|                 Core (core/)                      |  Audio, datasets, runner
+--------------------------------------------------+
|                 Evaluation (evaluation/)          |  Metrics computation
+--------------------------------------------------+
|                 Models (models/)                  |  Data structures
+--------------------------------------------------+
|         Telemetry (telemetry/) | Configs (configs/) |  Infrastructure
+--------------------------------------------------+
```

### Critical rule: Data flows downward

```
Transport -> Provider -> Metrics -> Reports
```

**NEVER** couple a Provider to a Transport. A provider must never know whether audio came from a file, Twilio, or a replay.

## 3. Module-by-Module Reference

### 3.1 Models (models/) - DONE

Pure Python dataclass objects. No logic. No I/O.

| File | Classes | Purpose |
|------|---------|---------|
| provider.py | ProviderConfig, ProviderState, ProviderType, ProviderStatus | Config for creating providers; runtime state tracking |
| result.py | BenchmarkResult | Single benchmark result containing transcript, latency, WER, entity accuracy |
| dataset.py | Entity, Sample, Dataset | Test dataset structure - each Sample has text, intent, entities, optional audio path |
| transcript.py | TranscriptChunk, Transcript | STT output - full text plus individual chunks with timing/confidence |
| latency.py | Latency | Timing metrics: connect_ms, first_partial_ms, ttfs_ms, final_ms, total_ms |

### 3.2 Core (core/) - MOSTLY DONE

| File | Singleton | Purpose | Status |
|------|-----------|---------|--------|
| config.py | cfg | Loads .env + YAML configs, exposes api_keys, enabled_providers | Done |
| audio.py | audio | Read WAV, chunk PCM, mu-law conversion, resampling | Done (minor bug: load/chunk_file are orphaned functions outside the class) |
| dataset.py | dataset_loader | Load versioned JSON datasets, auto-generate TTS audio per sample | Done |
| runner.py | - | BenchmarkRunner - runs samples through a provider, computes metrics | Done |
| reporter.py | reporter | Saves results as JSON, CSV, Markdown to timestamped run folders | Done |
| benchmark.py | - | - | Empty |
| metrics.py | - | - | Empty |
| utils.py | - | - | Empty |

### 3.3 Providers (providers/) - PARTIALLY DONE

| File | Class | Status |
|------|-------|--------|
| base.py | STTProvider (ABC) | Done - defines connect/start/stream/finish/close/transcribe_file |
| factory.py | ProviderFactory | Done - maps name to class |
| streaming/deepgram.py | DeepgramProvider | Done - full SDK integration |
| streaming/assemblyai.py | AssemblyAIProvider | Stub |
| streaming/gladia.py | GladiaProvider | Stub |
| streaming/speechmatics.py | SpeechmaticsProvider | Stub |
| batch/elevenlabs.py | ElevenLabsProvider | Stub |

Pattern to follow: Look at deepgram.py. Every provider must:
1. Accept ProviderConfig in __init__
2. Initialize its SDK client using config.api_key
3. Track self._chunks, self._text, self._latency, self._start, self._first
4. In _on_message: record TTFS on first result, append TranscriptChunk, call self.emit()
5. In transcribe_file: use the batch/REST API, return BenchmarkResult

### 3.4 Transports (transports/) - ALL STUBS

The transport layer delivers audio bytes to a provider. It abstracts the source.

| File | Class | What it should do |
|------|-------|-------------------|
| base.py | AudioTransport (ABC) | Interface defined: connect/stream/close |
| direct.py | DirectTransport | Read a WAV file, chunk it, yield PCM bytes directly |
| replay.py | ReplayTransport | Replay previously recorded call audio |
| twilio_media.py | TwilioMediaTransport | Receive mu-law audio from Twilio Media Streams WebSocket, decode to PCM |
| conversation_relay.py | ConversationRelayTransport | Receive audio from Twilio Conversation Relay |

### 3.5 Pipelines (pipelines/) - ALL STUBS

A pipeline wires Transport -> Provider -> Metrics -> Reports.

| File | Class | What it should do |
|------|-------|-------------------|
| direct_pipeline.py | DirectPipeline | Load audio -> DirectTransport -> stream to Provider -> evaluate -> report |
| twilio_pipeline.py | TwilioPipeline | Start WebSocket server -> receive Twilio audio -> Provider -> evaluate -> report |
| replay_pipeline.py | ReplayPipeline | Load recorded WAV -> ReplayTransport -> Provider -> evaluate -> report |
| conversation_pipeline.py | ConversationPipeline | Conversation Relay flow -> Provider -> evaluate -> report |

### 3.6 Services (services/) - MOSTLY STUBS

| File | Class | What it should do |
|------|-------|-------------------|
| tts_service.py | TTSService | Done - generates WAV via OpenAI TTS, caches by content hash |
| cache_service.py | CacheService | Manage cache for TTS audio, transcripts, and Twilio replays |
| report_service.py | ReportService | Coordinate report generation |
| export_service.py | ExportService | Export reports to charts, plots, PowerPoint |
| provider_service.py | ProviderService | Build ProviderConfig objects from YAML + .env, manage provider lifecycle |

### 3.7 Evaluation (evaluation/) - PARTIALLY DONE

| File | Function/Class | Status |
|------|---------------|--------|
| wer.py | calculate_wer() | Done |
| semantic.py | calculate_semantic_wer() | Done |
| entities.py | calculate_entity_accuracy() | Done |
| score.py | ProviderScorer | Done |
| ranking.py | ProviderRanking | Done |
| comparison.py | - | Stub - should compare providers, compute Twilio overhead |
| latency.py | - | Empty - should analyze latency distributions (p50, p95, p99) |
| reliability.py | - | Empty - should compute success/failure rates |
| cost.py | - | Empty - should compute per-provider cost estimates |

### 3.8 Telephony (telephony/) - ALL EMPTY

| File | What it should do |
|------|-------------------|
| media_streams/websocket_server.py | Accept Twilio Media Streams WebSocket connections |
| media_streams/twiml.py | Generate TwiML for call routing |
| media_streams/call_recorder.py | Record raw call audio for later replay |
| audio/mulaw.py | mu-law encode/decode utilities |
| audio/resampler.py | Resample between 8kHz (telephony) and 16kHz (STT) |

## 4. Configuration

### Environment Variables (.env)

```
OPENAI_API_KEY=sk-...          # Required for TTS generation
DEEPGRAM_API_KEY=...           # At least one STT provider required
ASSEMBLYAI_API_KEY=...
GLADIA_API_KEY=...
SPEECHMATICS_API_KEY=...
ELEVENLABS_API_KEY=...
TWILIO_ACCOUNT_SID=...         # Only for Twilio pipelines
TWILIO_AUTH_TOKEN=...
```

### YAML Configs (configs/)

Each provider has its own YAML with model name, sample rate, encoding, etc. The benchmark itself is configured in benchmark.yaml (dataset, voice, chunk_ms, retries, timeout).

## 5. Dataset Format

Datasets live in datasets/v1/, datasets/v2/, etc. Format:

```json
{
  "samples": [
    {
      "id": "sample_001",
      "text": "Hi, I'd like to schedule an appointment with Dr. Smith for next Tuesday.",
      "intent": "scheduling",
      "entities": [
        {"label": "doctor", "value": "Dr. Smith"},
        {"label": "day", "value": "Tuesday"}
      ]
    }
  ]
}
```

The DatasetLoader reads this, calls OpenAI TTS to generate WAV for each sample, caches it, and attaches the audio path to the Sample object.

## 6. Coding Conventions

- `from __future__ import annotations` at the top of every file
- `dataclass(slots=True)` for all models - no Pydantic
- Singletons at module level for services: cfg = Config(), audio = AudioManager(), tts = TTSService(), etc.
- Async: All provider and transport methods are async
- Type hints: Use `str | None` not `Optional[str]`
- PYTHONPATH: Must set PYTHONPATH=. when running from project root
- No hardcoded values in providers - everything comes from ProviderConfig or YAML

## 7. Key Dependencies

```
deepgram-sdk>=5.0.0    # Deepgram STT
python-dotenv           # .env loading
pyyaml                  # YAML config parsing
aiofiles                # Async file I/O
numpy                   # Audio processing
soundfile               # WAV reading
openai                  # TTS generation
jiwer                   # Word Error Rate calculation
rapidfuzz               # Fuzzy string matching
```

## 8. How to Run

```bash
cd benchmark
set PYTHONPATH=.
python -m cli              # Interactive menu
python tests/test_tts.py   # Test TTS generation
python tests/test_deepgram.py  # Test Deepgram connection
python tests/test_runner.py    # Run full benchmark
```
