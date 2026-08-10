"""
Vocalis API
-----------
Text-to-speech backend.

Endpoints:
  GET  /               -> health check
  GET  /voices?lang=..  -> list available voices (optionally filtered by locale)
  GET  /languages       -> list available locales
  POST /speak            -> { text, voice, rate, pitch } -> returns MP3 audio
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts
import asyncio
import time

app = FastAPI(title="Vocalis API", version="1.0.0")

# Allow the frontend to call this API from the browser.
# For tighter security later, replace "*" with your exact frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_voice_cache: list[dict] | None = None


def _friendly_name(short_name: str) -> str:
    # "en-US-AvaNeural" -> "Ava"
    # "en-US-AndrewMultilingualNeural" -> "Andrew (Multilingual)"
    name = short_name.split("-")[-1]
    name = name.replace("Neural", "")
    if "Multilingual" in name:
        name = name.replace("Multilingual", "") + " (Multilingual)"
    return name.strip()


@app.get("/")
async def root():
    return {"status": "ok", "message": "Vocalis API is running"}


@app.get("/voices")
async def get_voices(lang: str | None = None):
    global _voice_cache
    if _voice_cache is None:
        _voice_cache = await edge_tts.list_voices()

    voices = _voice_cache
    if lang:
        voices = [v for v in voices if v["Locale"].lower().startswith(lang.lower())]

    return [
        {
            "id": v["ShortName"],
            "name": _friendly_name(v["ShortName"]),
            "gender": v["Gender"],
            "locale": v["Locale"],
        }
        for v in voices
    ]


@app.get("/languages")
async def get_languages():
    global _voice_cache
    if _voice_cache is None:
        _voice_cache = await edge_tts.list_voices()
    return sorted({v["Locale"] for v in _voice_cache})


class SpeakRequest(BaseModel):
    text: str
    voice: str = "en-US-AnaNeural"
    rate: str = "+0%"    # e.g. "-50%", "+100%"
    pitch: str = "+0Hz"  # e.g. "-50Hz", "+50Hz"


@app.post("/speak")
async def speak(req: SpeakRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > 100000:
        raise HTTPException(status_code=400, detail="Text too long (max 100,000 characters)")

    async def _synthesize() -> bytes:
        t0 = time.perf_counter()
        communicate = edge_tts.Communicate(text, req.voice, rate=req.rate, pitch=req.pitch)
        audio = bytearray()
        chunk_count = 0
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
                chunk_count += 1
        elapsed = time.perf_counter() - t0
        print(f"[speak] voice={req.voice} chars={len(text)} chunks={chunk_count} "
              f"bytes={len(audio)} elapsed={elapsed:.2f}s", flush=True)
        return bytes(audio)

    try:
        req_t0 = time.perf_counter()
        # 45s is generous for normal-length text; if it takes longer, something
        # upstream (network route to Microsoft's TTS service) is the bottleneck.
        audio_bytes = await asyncio.wait_for(_synthesize(), timeout=55)
        print(f"[speak] total request time={time.perf_counter()-req_t0:.2f}s", flush=True)
    except asyncio.TimeoutError:
        print(f"[speak] TIMED OUT after 45s for voice={req.voice} chars={len(text)}", flush=True)
        raise HTTPException(
            status_code=504,
            detail="Voice generation timed out. Try shorter text, or try again in a moment.",
        )

    if not audio_bytes:
        raise HTTPException(status_code=502, detail="No audio was generated. Try again.")

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )
