# AI Receptionist STT Benchmarking Framework

A comprehensive benchmarking framework for evaluating Speech-to-Text (STT) providers in real-world telephony use cases, specifically designed for AI Receptionists and Voice Agents.

## Overview

This framework answers the critical question: *"Which STT provider gives us the best transcription quality, lowest latency, and highest reliability — both in direct API mode and when audio arrives through Twilio?"*

It runs audio samples against multiple leading STT models, evaluates the outputs for accuracy and latency, and generates beautiful, interactive HTML dashboards and comprehensive white papers to visualize the results.

### Supported Providers
* **Deepgram** (Nova 2 / General)
* **AssemblyAI** (Streaming)
* **Speechmatics**
* **Gladia**
* **ElevenLabs**

## Key Features

* **Dual Pipeline Evaluation**: Tests providers in a pristine `Direct` pipeline (bypassing telephony constraints) and a realistic `Twilio` pipeline (simulating 8kHz mu-law audio streamed over WebSockets).
* **Advanced Metrics**: Measures traditional Word Error Rate (WER), Semantic WER (for meaning-based accuracy), Entity Accuracy (did it get the name right?), and Time To First Symbol (TTFS) latency.
* **Interactive Dashboards**: Automatically generates Chart.js powered HTML dashboards and a Market Comparison white paper with robust data visualization.
* **TTS Audio Generation**: Includes scripts to test and synthesize expressive audio samples using AWS Polly (SSML/Neural) and Fish Audio.

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
   cd YOUR-REPO-NAME
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   Create a `.env` file in the root directory and add your provider keys (never commit this file):
   ```env
   OPENAI_API_KEY=your_key_here
   DEEPGRAM_API_KEY=your_key_here
   ASSEMBLYAI_API_KEY=your_key_here
   ELEVENLABS_API_KEY=your_key_here
   SPEECHMATICS_API_KEY=your_key_here
   GLADIA_API_KEY=your_key_here
   ```

## Usage

*To run a full benchmark and generate reports, use the CLI (example commands based on project structure):*

```bash
# Run the benchmark
python cli.py run --pipeline direct

# Generate HTML Dashboard & Market Comparison White Paper
python cli.py report
```

### TTS Samples
If you want to generate the placeholder TTS samples (Twilio/Polly, AWS Polly Direct, Fish Audio), configure your AWS and Fish Audio keys in `.env` and run:
```bash
python generate_tts_samples.py
```
*Outputs will be saved in the `tts_samples/` directory.*

## Project Structure
* `cli/` - Command-line interface definitions and commands.
* `core/` - Configuration management and environment loading.
* `evaluation/` - Metric calculation logic (WER, Semantic WER, latency).
* `pipelines/` - Execution paths (Direct vs. Twilio).
* `providers/` - Standardized interfaces for each STT vendor.
* `services/` - Caching, text normalization, and provider orchestration.
* `storage/` - Output directory for cached audio, JSON transcripts, and HTML reports.
* `dashboard.py` - HTML and Chart.js generation engine for the reports.
