from __future__ import annotations
import asyncio
import time
import json
import base64
import websockets
from pathlib import Path

from models.latency import Latency
from models.result import BenchmarkResult
from models.transcript import Transcript, TranscriptChunk
from providers.base import STTProvider

class GladiaProvider(STTProvider):
    def __init__(self, config):
        super().__init__(config)
        self.ws = None
        self._chunks = []
        self._text = ""
        self._accumulated_text = ""
        self._latency = Latency()
        self._start = 0
        self._first = False
        self._receive_task = None

    async def connect(self):
        self.state.connected = False
        url = "wss://api.gladia.io/audio/text/audio-transcription"
        headers = {"x-gladia-key": self.config.api_key}
        
        self.ws = await websockets.connect(url, additional_headers=headers, open_timeout=None)
        
        # v1 might require an initial setup or we can just start sending frames
        init_msg = {
            "x_gladia_key": self.config.api_key,
            "sample_rate": 16000,
            "encoding": "wav"
        }
        await self.ws.send(json.dumps(init_msg))
        
        self._receive_task = asyncio.create_task(self._receive_loop())
        self.state.connected = True

    async def _receive_loop(self):
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                
                # Check for transcription in Gladia v1
                if "transcription" in data:
                    text = data.get("transcription", "").strip()
                    if not text:
                        continue

                    now = time.perf_counter()
                    if not self._first:
                        self._latency.ttfs_ms = (now - self._start) * 1000
                        self._first = True

                    is_final = data.get("type") == "final"
                    
                    if is_final:
                        self._accumulated_text = (self._accumulated_text + " " + text).strip()
                        self._text = self._accumulated_text
                    else:
                        self._text = (self._accumulated_text + " " + text).strip()

                    self._chunks.append(
                        TranscriptChunk(
                            text=text,
                            is_final=is_final,
                            start=data.get("time_begin", 0),
                            end=data.get("time_end", 0),
                            confidence=0.9, # Gladia v1 doesn't consistently provide confidence per chunk
                        )
                    )

                    await self.emit(text, is_final)
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Gladia WS error: {e}")

    async def start(self):
        self._chunks.clear()
        self._text = ""
        self._accumulated_text = ""
        self._start = time.perf_counter()
        self._first = False

    async def stream(self, chunk: bytes):
        if self.ws:
            payload = json.dumps({"frames": base64.b64encode(chunk).decode("utf-8")})
            await self.ws.send(payload)

    async def finish(self):
        if self.ws:
            # We can't guarantee how Gladia v1 terminates, so just wait a bit
            await asyncio.sleep(1.0)

    async def close(self):
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.state.connected = False

    async def transcribe_file(self, audio: Path) -> BenchmarkResult:
        import httpx
        url = "https://api.gladia.io/v2/transcription/"
        headers = {"X-Gladia-Key": self.config.api_key}
        
        async with httpx.AsyncClient() as client:
            with open(audio, "rb") as f:
                upload_resp = await client.post(
                    "https://api.gladia.io/v2/upload", 
                    headers=headers, 
                    files={"audio": f}
                )
            audio_url = upload_resp.json().get("audio_url")
            
            req = {"audio_url": audio_url}
            tx_resp = await client.post(url, headers=headers, json=req)
            tx_id = tx_resp.json()["id"]
            
            while True:
                poll_resp = await client.get(f"{url}{tx_id}", headers=headers)
                status = poll_resp.json()["status"]
                if status == "done":
                    transcript = poll_resp.json()["result"]["transcription"]["full_transcript"]
                    break
                elif status == "error":
                    transcript = ""
                    break
                await asyncio.sleep(1)
                
        return BenchmarkResult(
            provider="Gladia",
            transcript=Transcript(provider="Gladia", text=transcript, chunks=[]),
            latency=Latency(),
            wer=0.0,
            semantic_wer=0.0,
            entity_accuracy=0.0,
            success=True
        )
