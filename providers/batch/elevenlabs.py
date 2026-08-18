from __future__ import annotations
import asyncio
import time
import io
import wave
import httpx
from pathlib import Path

from models.latency import Latency
from models.result import BenchmarkResult
from models.transcript import Transcript, TranscriptChunk
from providers.base import STTProvider

def create_wav_buffer(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()

class ElevenLabsProvider(STTProvider):
    def __init__(self, config):
        super().__init__(config)
        self._buffer = bytearray()
        self._latency = Latency()
        self._start = 0

    async def connect(self):
        self.state.connected = True

    async def start(self):
        self._buffer.clear()
        self._start = time.perf_counter()
        
    async def stream(self, chunk: bytes):
        # ElevenLabs doesn't have a streaming WS, so we buffer the chunks
        self._buffer.extend(chunk)

    async def finish(self):
        # We now have the complete audio stream.
        if not self._buffer:
            return
            
        wav_data = create_wav_buffer(self._buffer)
        
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": self.config.api_key}
        files = {"file": ("audio.wav", wav_data, "audio/wav")}
        data = {"model_id": "scribe_v1"}
        
        try:
            req_start = time.perf_counter()
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, files=files, data=data, timeout=30.0)
                
            response.raise_for_status()
            text = response.json().get("text", "").strip()
            
            now = time.perf_counter()
            # For a batch-simulated provider, TTFS is effectively the API request latency
            self._latency.ttfs_ms = (now - req_start) * 1000
            self._text = text
            self._chunks.append(
                TranscriptChunk(
                    text=text,
                    is_final=True,
                    start=0.0,
                    end=0.0,
                    confidence=0.9
                )
            )
            await self.emit(text, final=True)
            
        except Exception as e:
            print(f"ElevenLabs HTTP error: {e}")

    async def close(self):
        self.state.connected = False
        self._buffer.clear()

    async def transcribe_file(self, audio: Path) -> BenchmarkResult:
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": self.config.api_key}
        
        async with httpx.AsyncClient() as client:
            with open(audio, "rb") as f:
                files = {"file": (audio.name, f, "audio/wav")}
                data = {"model_id": "scribe_v1"}
                response = await client.post(url, headers=headers, files=files, data=data, timeout=30.0)
                
            transcript = response.json().get("text", "")
            
        return BenchmarkResult(
            provider="ElevenLabs",
            transcript=Transcript(provider="ElevenLabs", text=transcript, chunks=[]),
            latency=Latency(),
            wer=0.0,
            semantic_wer=0.0,
            entity_accuracy=0.0,
            success=True
        )
