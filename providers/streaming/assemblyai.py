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

class AssemblyAIProvider(STTProvider):
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
        url = "wss://streaming.assemblyai.com/v3/ws?sample_rate=16000"
        headers = {"Authorization": self.config.api_key}
        
        self.ws = await websockets.connect(url, additional_headers=headers, open_timeout=None)
        
        # Wait for SessionBegins
        session_begins = await self.ws.recv()
        data = json.loads(session_begins)
        if data.get("type") != "Begin" and data.get("message_type") != "SessionBegins":
            print(f"AssemblyAI failed to begin session: {data}")
        
        self._receive_task = asyncio.create_task(self._receive_loop())
        self.state.connected = True

    async def _receive_loop(self):
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                msg_type = data.get("type") or data.get("message_type")
                
                if msg_type == "Turn":
                    text = data.get("transcript", "")
                    if not text:
                        continue

                    now = time.perf_counter()
                    if not self._first:
                        self._latency.ttfs_ms = (now - self._start) * 1000
                        self._first = True

                    is_final = data.get("end_of_turn", False)
                    
                    if is_final:
                        self._accumulated_text = (self._accumulated_text + " " + text).strip()
                        self._text = self._accumulated_text
                    else:
                        self._text = (self._accumulated_text + " " + text).strip()

                    self._chunks.append(
                        TranscriptChunk(
                            text=text,
                            is_final=is_final,
                            start=data.get("audio_start", 0) / 1000.0,
                            end=data.get("audio_end", 0) / 1000.0,
                            confidence=data.get("confidence", 0.0),
                        )
                    )

                    await self.emit(text, is_final)
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"AssemblyAI WS error: {e}")

    async def start(self):
        self._chunks.clear()
        self._text = ""
        self._accumulated_text = ""
        self._start = time.perf_counter()
        self._first = False

    async def stream(self, chunk: bytes):
        if self.ws:
            # AssemblyAI v3 expects raw PCM bytes
            await self.ws.send(chunk)

    async def finish(self):
        if self.ws:
            # Send close signal
            await self.ws.send(json.dumps({"terminate_session": True}))
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
        url = "https://api.assemblyai.com/v2/upload"
        headers = {"Authorization": self.config.api_key}
        
        async with httpx.AsyncClient() as client:
            with open(audio, "rb") as f:
                upload_resp = await client.post(url, headers=headers, content=f.read())
            audio_url = upload_resp.json()["upload_url"]
            
            req = {"audio_url": audio_url}
            tx_url = "https://api.assemblyai.com/v2/transcript"
            tx_resp = await client.post(tx_url, headers=headers, json=req)
            tx_id = tx_resp.json()["id"]
            
            while True:
                poll_resp = await client.get(f"{tx_url}/{tx_id}", headers=headers)
                status = poll_resp.json()["status"]
                if status == "completed":
                    transcript = poll_resp.json()["text"]
                    break
                elif status == "error":
                    transcript = ""
                    break
                await asyncio.sleep(1)
                
        return BenchmarkResult(
            provider="AssemblyAI",
            transcript=Transcript(provider="AssemblyAI", text=transcript, chunks=[]),
            latency=Latency(),
            wer=0.0,
            semantic_wer=0.0,
            entity_accuracy=0.0,
            success=True
        )
