"""
Vocalis API
-----------
Text-to-speech backend.

Endpoints:
  GET  /voices?lang=en-US   -> list available voices
  POST /speak                -> { text, voice, rate, pitch } -> streams MP3 audio
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts

app = FastAPI(title="Open Voice TTS API", version="1.0.0")

# Allow your frontend (any origin) to call this API.
# In production, replace "*" with your actual frontend URL for safety.
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
    """List all voices, optionally filtered by locale prefix, e.g. lang=en-US"""
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
    """List distinct locales available, e.g. en-US, ur-PK, hi-IN"""
    global _voice_cache
    if _voice_cache is None:
        _voice_cache = await edge_tts.list_voices()
    locales = sorted({v["Locale"] for v in _voice_cache})
    return locales


class SpeakRequest(BaseModel):
    text: str
    voice: str = "en-US-AvaNeural"
    rate: str = "+0%"    # e.g. "-20%", "+15%"
    pitch: str = "+0Hz"  # e.g. "-10Hz", "+10Hz"


@app.post("/speak")
async def speak(req: SpeakRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")

    communicate = edge_tts.Communicate(text, req.voice, rate=req.rate, pitch=req.pitch)
    audio_bytes = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])

    if not audio_bytes:
        raise HTTPException(status_code=502, detail="No audio was generated. Try again.")

    return Response(
        content=bytes(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )
