from __future__ import annotations

import asyncio
import time
import json
import websockets
from pathlib import Path

from models.latency import Latency
from models.result import BenchmarkResult
from models.transcript import Transcript, TranscriptChunk
from providers.base import STTProvider

class DeepgramProvider(STTProvider):

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
        url = f"wss://api.deepgram.com/v1/listen?model={self.config.model}&encoding=linear16&sample_rate=16000&interim_results=true&punctuate=true"
        headers = {"Authorization": f"Token {self.config.api_key}"}
        
        self.ws = await websockets.connect(url, additional_headers=headers, open_timeout=None)
        
        # Start a background task to receive messages
        self._receive_task = asyncio.create_task(self._receive_loop())
        self.state.connected = True

    async def _receive_loop(self):
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                
                # Check for transcript results
                if data.get("type") == "Results":
                    channels = data.get("channel", {})
                    alternatives = channels.get("alternatives", [])
                    if not alternatives:
                        continue
                        
                    alt = alternatives[0]
                    text = alt.get("transcript", "")
                    
                    if not text:
                        continue

                    now = time.perf_counter()
                    if not self._first:
                        self._latency.ttfs_ms = (now - self._start) * 1000
                        self._first = True

                    is_final = data.get("is_final", False)
                    
                    if is_final:
                        self._accumulated_text = (self._accumulated_text + " " + text).strip()
                        self._text = self._accumulated_text
                    else:
                        self._text = (self._accumulated_text + " " + text).strip()

                    self._chunks.append(
                        TranscriptChunk(
                            text=text,
                            is_final=is_final,
                            start=data.get("start", 0),
                            end=data.get("duration", 0),
                            confidence=alt.get("confidence", 0),
                        )
                    )

                    await self.emit(text, is_final)
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Deepgram WS error: {e}")

    async def start(self):
        self._chunks.clear()
        self._text = ""
        self._accumulated_text = ""
        self._start = time.perf_counter()
        self._first = False

    async def stream(self, chunk: bytes):
        if self.ws:
            await self.ws.send(chunk)

    async def finish(self):
        if self.ws:
            # Send close stream message to let Deepgram know we are done
            await self.ws.send(json.dumps({"type": "CloseStream"}))
            # Wait a bit to ensure the final transcript is received
            await asyncio.sleep(1.0)

    async def close(self):
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.state.connected = False

    async def transcribe_file(self, audio: Path):
        # We can fallback to deepgram sdk for batch transcription, or just do an http request
        import httpx
        with open(audio, "rb") as f:
            data = f.read()
            
        url = f"https://api.deepgram.com/v1/listen?model={self.config.model}"
        headers = {
            "Authorization": f"Token {self.config.api_key}",
            "Content-Type": "audio/wav"
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, content=data, timeout=30.0)
            resp_data = resp.json()
            
        transcript = resp_data["results"]["channels"][0]["alternatives"][0]["transcript"]

        return BenchmarkResult(
            provider="Deepgram",
            transcript=Transcript(
                provider="Deepgram",
                text=transcript,
                chunks=[],
            ),
            latency=Latency(),
            wer=0,
            semantic_wer=0,
            entity_accuracy=0,
            success=True,
        )