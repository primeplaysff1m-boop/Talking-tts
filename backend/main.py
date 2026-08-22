"""
Vocalis API
-----------
Text-to-speech backend.

Endpoints:
  GET  /                -> health check
  GET  /voices?lang=..  -> list available voices (optionally filtered by locale)
  GET  /languages       -> list available locales
  POST /speak           -> { text, voice, rate, pitch } -> complete MP3 audio
  POST /speak/stream    -> the same request, streamed as MP3 for progressive playback
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

import edge_tts
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Vocalis API", version="1.2.0")

# The frontend is intentionally static and can be hosted separately.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_voice_cache: list[dict] | None = None
MAX_TEXT_LENGTH = 100_000
SYNTHESIS_TIMEOUT_SECONDS = 55
VOICE_CACHE_HEADERS = {"Cache-Control": "public, max-age=3600, stale-while-revalidate=86400"}
AUDIO_HEADERS = {
    "Content-Disposition": "inline; filename=speech.mp3",
    "Cache-Control": "no-store",
}
STREAM_HEADERS = {
    **AUDIO_HEADERS,
    # Reverse proxies that honor this header should pass audio through as it arrives.
    "X-Accel-Buffering": "no",
}


def _friendly_name(short_name: str) -> str:
    # "en-US-AvaNeural" -> "Ava"
    # "en-US-AndrewMultilingualNeural" -> "Andrew (Multilingual)"
    name = short_name.split("-")[-1]
    name = name.replace("Neural", "")
    if "Multilingual" in name:
        name = name.replace("Multilingual", "") + " (Multilingual)"
    return name.strip()


async def _load_voices() -> list[dict]:
    """Load the upstream catalog once per warm instance."""
    global _voice_cache
    if _voice_cache is None:
        _voice_cache = await edge_tts.list_voices()
    return _voice_cache


async def _voice_payload(lang: str | None = None) -> list[dict]:
    voices = await _load_voices()
    if lang:
        voices = [voice for voice in voices if voice["Locale"].lower().startswith(lang.lower())]
    return [
        {
            "id": voice["ShortName"],
            "name": _friendly_name(voice["ShortName"]),
            "gender": voice["Gender"],
            "locale": voice["Locale"],
        }
        for voice in voices
    ]


@app.get("/")
async def root():
    return {"status": "ok", "message": "Vocalis API is running"}


@app.get("/voices")
async def get_voices(lang: str | None = None):
    try:
        return JSONResponse(content=await _voice_payload(lang), headers=VOICE_CACHE_HEADERS)
    except Exception as error:
        print(f"[voices] catalog lookup failed: {error}", flush=True)
        raise HTTPException(status_code=503, detail="Voice catalog is temporarily unavailable. Please try again shortly.")


@app.get("/languages")
async def get_languages():
    try:
        voices = await _load_voices()
        locales = sorted({voice["Locale"] for voice in voices})
        return JSONResponse(content=locales, headers=VOICE_CACHE_HEADERS)
    except Exception as error:
        print(f"[languages] catalog lookup failed: {error}", flush=True)
        raise HTTPException(status_code=503, detail="Voice catalog is temporarily unavailable. Please try again shortly.")


class SpeakRequest(BaseModel):
    text: str
    voice: str = "en-US-AnaNeural"
    rate: str = "+0%"    # e.g. "-50%", "+100%"
    pitch: str = "+0Hz"  # e.g. "-50Hz", "+50Hz"


def _validated_text(req: SpeakRequest) -> str:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail=f"Text too long (max {MAX_TEXT_LENGTH:,} characters)")
    return text


async def _open_audio_stream(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
) -> tuple[AsyncIterator[dict], bytes]:
    """Return an edge-tts iterator after eagerly obtaining its first audio frame.

    Waiting for the first frame before sending the HTTP response means upstream
    connection failures can still return a useful HTTP error rather than a
    partially opened 200 response. The iterator is then reused by either the
    buffered or progressive endpoint.
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    stream = communicate.stream()
    async for chunk in stream:
        if chunk["type"] == "audio":
            return stream, chunk["data"]
    raise RuntimeError("No audio was generated")


async def _collect_audio(text: str, req: SpeakRequest) -> bytes:
    started_at = time.perf_counter()
    stream, first_audio = await _open_audio_stream(text, req.voice, req.rate, req.pitch)
    audio = bytearray(first_audio)
    chunk_count = 1
    async for chunk in stream:
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
            chunk_count += 1
    elapsed = time.perf_counter() - started_at
    print(
        f"[speak] voice={req.voice} chars={len(text)} chunks={chunk_count} "
        f"bytes={len(audio)} elapsed={elapsed:.2f}s",
        flush=True,
    )
    return bytes(audio)


@app.post("/speak")
async def speak(req: SpeakRequest):
    """Return a complete MP3 response for broad compatibility."""
    text = _validated_text(req)
    try:
        audio_bytes = await asyncio.wait_for(
            _collect_audio(text, req), timeout=SYNTHESIS_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        print(f"[speak] TIMED OUT after {SYNTHESIS_TIMEOUT_SECONDS}s for voice={req.voice} chars={len(text)}", flush=True)
        raise HTTPException(
            status_code=504,
            detail="Voice generation timed out. Try shorter text, or try again in a moment.",
        )
    except HTTPException:
        raise
    except Exception as error:
        print(f"[speak] upstream error for voice={req.voice}: {error}", flush=True)
        raise HTTPException(status_code=502, detail="No audio was generated. Try again.")

    if not audio_bytes:
        raise HTTPException(status_code=502, detail="No audio was generated. Try again.")

    return Response(content=audio_bytes, media_type="audio/mpeg", headers=AUDIO_HEADERS)


@app.post("/speak/stream")
async def speak_stream(req: SpeakRequest):
    """Stream MP3 chunks as they arrive from edge-tts.

    The existing /speak endpoint remains unchanged for callers that need a
    complete Blob. The studio uses this endpoint when the browser supports the
    Media Source API, and safely falls back to /speak everywhere else.
    """
    text = _validated_text(req)
    started_at = time.perf_counter()
    try:
        stream, first_audio = await asyncio.wait_for(
            _open_audio_stream(text, req.voice, req.rate, req.pitch),
            timeout=SYNTHESIS_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        print(f"[speak-stream] first audio timed out after {SYNTHESIS_TIMEOUT_SECONDS}s for voice={req.voice} chars={len(text)}", flush=True)
        raise HTTPException(
            status_code=504,
            detail="Voice generation timed out. Try shorter text, or try again in a moment.",
        )
    except HTTPException:
        raise
    except Exception as error:
        print(f"[speak-stream] upstream error before first frame for voice={req.voice}: {error}", flush=True)
        raise HTTPException(status_code=502, detail="No audio was generated. Try again.")

    async def audio_chunks() -> AsyncIterator[bytes]:
        chunk_count = 1
        bytes_sent = len(first_audio)
        try:
            yield first_audio
            remaining_time = max(0.1, SYNTHESIS_TIMEOUT_SECONDS - (time.perf_counter() - started_at))
            async with asyncio.timeout(remaining_time):
                async for chunk in stream:
                    if chunk["type"] == "audio":
                        chunk_count += 1
                        bytes_sent += len(chunk["data"])
                        yield chunk["data"]
        except asyncio.TimeoutError:
            # Headers may already be sent, so an HTTP 504 is no longer possible.
            # End the stream and log it rather than sending malformed audio data.
            print(f"[speak-stream] TIMED OUT while streaming voice={req.voice} chars={len(text)}", flush=True)
        except asyncio.CancelledError:
            # Client cancellation should stop upstream generation quickly.
            raise
        except Exception as error:
            print(f"[speak-stream] upstream stream error for voice={req.voice}: {error}", flush=True)
        finally:
            elapsed = time.perf_counter() - started_at
            print(
                f"[speak-stream] voice={req.voice} chars={len(text)} chunks={chunk_count} "
                f"bytes={bytes_sent} elapsed={elapsed:.2f}s",
                flush=True,
            )

    return StreamingResponse(audio_chunks(), media_type="audio/mpeg", headers=STREAM_HEADERS)
