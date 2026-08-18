from __future__ import annotations
import asyncio
import time
import io
import wave
import speech_recognition as sr
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

class GooglePublicProvider(STTProvider):
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
        # Accumulate chunks since this is a batch provider
        self._buffer.extend(chunk)

    async def finish(self):
        if not self._buffer:
            return
            
        wav_data = create_wav_buffer(self._buffer)
        
        # Use a thread executor because speech_recognition blocks
        loop = asyncio.get_running_loop()
        
        def run_recognition():
            recognizer = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(wav_data)) as source:
                audio = recognizer.record(source)
            try:
                # This uses the undocumented public API endpoint for Google STT
                return recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return ""
            except sr.RequestError as e:
                print(f"Google Public API request error: {e}")
                return ""

        req_start = time.perf_counter()
        text = await loop.run_in_executor(None, run_recognition)
        now = time.perf_counter()
        
        # Simulated TTFS based on total request round-trip time
        self._latency.ttfs_ms = (now - req_start) * 1000
        self._text = text
        self._chunks.append(
            TranscriptChunk(
                text=text,
                is_final=True,
                start=0.0,
                end=0.0,
                confidence=1.0
            )
        )
        await self.emit(text, final=True)

    async def close(self):
        self.state.connected = False
        self._buffer.clear()

    async def transcribe_file(self, audio: Path) -> BenchmarkResult:
        # Not strictly needed since DirectPipeline uses start/stream/finish, 
        # but returning a stub to conform to STTProvider if called directly.
        return BenchmarkResult(
            provider="GooglePublic",
            transcript=Transcript(provider="GooglePublic", text="", chunks=[]),
            latency=Latency(),
            wer=0.0,
            semantic_wer=0.0,
            entity_accuracy=0.0,
            success=True
        )
