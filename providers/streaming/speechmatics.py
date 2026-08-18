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

class SpeechmaticsProvider(STTProvider):
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
        url = "wss://eu2.rt.speechmatics.com/v2/en"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        
        self.ws = await websockets.connect(url, additional_headers=headers, open_timeout=None)
        
        init_msg = {
            "message": "StartRecognition",
            "audio_format": {
                "type": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 16000
            },
            "transcription_config": {
                "language": "en",
                "enable_partials": True
            }
        }
        await self.ws.send(json.dumps(init_msg))
        
        # Wait for RecognitionStarted
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get("message") not in ("RecognitionStarted", "Info"):
            print(f"Speechmatics failed to start: {data}")
        
        self._receive_task = asyncio.create_task(self._receive_loop())
        self.state.connected = True

    async def _receive_loop(self):
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                msg_type = data.get("message")
                
                if msg_type in ("AddTranscript", "AddPartialTranscript"):
                    results = data.get("results", [])
                    if not results:
                        continue
                        
                    # Speechmatics splits results into words/tokens
                    # We need to reconstruct the transcript from the tokens
                    text = ""
                    confidence = 0.0
                    for res in results:
                        word_conf = res.get("alternatives", [{}])[0].get("confidence", 0.0)
                        word = res.get("alternatives", [{}])[0].get("content", "")
                        # attach spaces appropriately based on token type if needed
                        text += word + " "
                        confidence = max(confidence, word_conf)
                    
                    text = text.strip()
                    if not text:
                        continue

                    now = time.perf_counter()
                    if not self._first:
                        self._latency.ttfs_ms = (now - self._start) * 1000
                        self._first = True

                    is_final = (msg_type == "AddTranscript")
                    
                    if is_final:
                        self._accumulated_text = (self._accumulated_text + " " + text).strip()
                        self._text = self._accumulated_text
                    else:
                        self._text = (self._accumulated_text + " " + text).strip()

                    meta = data.get("metadata", {})
                    self._chunks.append(
                        TranscriptChunk(
                            text=text,
                            is_final=is_final,
                            start=meta.get("start_time", 0),
                            end=meta.get("end_time", 0),
                            confidence=confidence,
                        )
                    )

                    await self.emit(text, is_final)
                    
                elif msg_type == "EndOfTranscript":
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Speechmatics WS error: {e}")

    async def start(self):
        self._chunks.clear()
        self._text = ""
        self._accumulated_text = ""
        self._start = time.perf_counter()
        self._first = False

    async def stream(self, chunk: bytes):
        if self.ws:
            # Speechmatics expects binary frames for audio
            await self.ws.send(chunk)

    async def finish(self):
        if self.ws:
            await self.ws.send(json.dumps({"message": "EndOfStream"}))
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
        url = "https://asr.api.speechmatics.com/v2/jobs/"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        
        async with httpx.AsyncClient() as client:
            config = {
                "type": "transcription",
                "transcription_config": {"language": "en"}
            }
            data = {"config": json.dumps(config)}
            with open(audio, "rb") as f:
                files = {"data_file": f}
                resp = await client.post(url, headers=headers, data=data, files=files)
            
            job_id = resp.json()["id"]
            
            while True:
                poll_resp = await client.get(f"{url}{job_id}/", headers=headers)
                status = poll_resp.json()["job"]["status"]
                if status == "done":
                    res_resp = await client.get(f"{url}{job_id}/transcript", headers=headers)
                    transcript = ""
                    for res in res_resp.json().get("results", []):
                        transcript += res["alternatives"][0]["content"] + " "
                    transcript = transcript.strip()
                    break
                elif status in ("rejected", "deleted", "expired"):
                    transcript = ""
                    break
                await asyncio.sleep(1)
                
        return BenchmarkResult(
            provider="Speechmatics",
            transcript=Transcript(provider="Speechmatics", text=transcript, chunks=[]),
            latency=Latency(),
            wer=0.0,
            semantic_wer=0.0,
            entity_accuracy=0.0,
            success=True
        )
