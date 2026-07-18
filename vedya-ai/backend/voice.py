"""
ElevenLabs voice helpers: TTS (speak explanations) + STT (voice intake).
Uses REST via httpx so we do not require the ElevenLabs SDK.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVEN_STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"

# Public multilingual-capable default voice (Rachel). Override via env.
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
TTS_MODEL = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2")
STT_MODEL = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v2")

# Ayurvedic keyterms improve STT for classical vocabulary
AYURVEDA_KEYTERMS = [
    "Jvara", "Kasa", "Pinasa", "Shotha", "Prameha", "Madhumeha",
    "Punarnavadi", "Vyaghryadi", "Kashaya", "Kashayam", "Asava", "Arishta",
    "Ghrita", "Abhaya", "Jatyadi", "Santapa", "Pratishyaya", "Shwasa",
    "Vaidya", "Ayurveda", "Rasa", "Virya", "Vipaka",
]


def voice_configured() -> bool:
    return bool(ELEVEN_API_KEY)


def voice_status() -> dict:
    return {
        "configured": voice_configured(),
        "tts_model": TTS_MODEL,
        "stt_model": STT_MODEL,
        "default_voice_id": DEFAULT_VOICE_ID,
        "features": [
            "text_to_speech",
            "speech_to_text",
            "multilingual_narration",
            "ayurveda_keyterms",
            "compare_narration",
            "preset_case_readaloud",
        ],
    }


async def synthesize_speech(
    text: str,
    *,
    voice_id: Optional[str] = None,
    locale: str = "en",
) -> bytes:
    if not ELEVEN_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    if not text or not text.strip():
        raise ValueError("Empty text")

    # Keep payloads short for interactive listen buttons
    cleaned = " ".join(text.split())
    if len(cleaned) > 1200:
        cleaned = cleaned[:1200] + "…"

    vid = voice_id or DEFAULT_VOICE_ID
    language_code = locale if locale in {"en", "hi", "gu"} else "en"

    payload = {
        "text": cleaned,
        "model_id": TTS_MODEL,
    }
    # language_code supported on flash/turbo; multilingual_v2 ignores unknown fields safely
    if TTS_MODEL.startswith("eleven_flash") or TTS_MODEL.startswith("eleven_turbo"):
        payload["language_code"] = language_code

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{ELEVEN_TTS_URL}/{vid}",
            headers=headers,
            params={"output_format": "mp3_44100_128"},
            json=payload,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"ElevenLabs TTS error {resp.status_code}: {resp.text[:300]}")
        return resp.content


async def transcribe_audio(
    file_bytes: bytes,
    filename: str = "audio.webm",
    *,
    locale: str = "en",
) -> dict:
    if not ELEVEN_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    if not file_bytes:
        raise ValueError("Empty audio")

    language_code = locale if locale in {"en", "hi", "gu"} else None
    headers = {"xi-api-key": ELEVEN_API_KEY}

    # Prefer webm/wav content types from browser MediaRecorder
    content_type = "audio/webm"
    lower = filename.lower()
    if lower.endswith(".wav"):
        content_type = "audio/wav"
    elif lower.endswith(".mp3"):
        content_type = "audio/mpeg"
    elif lower.endswith(".m4a"):
        content_type = "audio/mp4"

    data: list[tuple[str, str]] = [("model_id", STT_MODEL)]
    if language_code:
        data.append(("language_code", language_code))
    for term in AYURVEDA_KEYTERMS:
        data.append(("keyterms", term))

    files = {"file": (filename, file_bytes, content_type)}

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(ELEVEN_STT_URL, headers=headers, data=data, files=files)
        if resp.status_code >= 400:
            raise RuntimeError(f"ElevenLabs STT error {resp.status_code}: {resp.text[:400]}")
        payload = resp.json()
        text = payload.get("text") or payload.get("transcript") or ""
        return {
            "text": text.strip(),
            "language_code": payload.get("language_code") or language_code,
            "raw": {k: payload.get(k) for k in ("language_code", "language_probability") if k in payload},
        }


def build_listen_script(
    *,
    yoga_name: str,
    kalpana: str | None,
    summary: str,
    winner_reason: str | None = None,
    locale: str = "en",
) -> str:
    locale = locale if locale in {"en", "hi", "gu"} else "en"
    form = kalpana or ""
    if locale == "hi":
        parts = [f"शीर्ष अनुशंसा: {yoga_name}"]
        if form:
            parts.append(f"कल्पना: {form}")
        if summary:
            parts.append(summary)
        if winner_reason:
            parts.append(f"तुलना: {winner_reason}")
        parts.append("यह शैक्षिक निर्णय सहायता है, निदान या नुस्खा नहीं।")
        return " ".join(parts)
    if locale == "gu":
        parts = [f"ટોચની ભલામણ: {yoga_name}"]
        if form:
            parts.append(f"કલ્પના: {form}")
        if summary:
            parts.append(summary)
        if winner_reason:
            parts.append(f"સરખામણી: {winner_reason}")
        parts.append("આ શૈક્ષણિક નિર્ણય સહાય છે, નિદાન કે પ્રિસ્ક્રિપ્શન નથી.")
        return " ".join(parts)
    parts = [f"Top recommendation: {yoga_name}"]
    if form:
        parts.append(f"Form: {form}")
    if summary:
        parts.append(summary)
    if winner_reason:
        parts.append(f"Comparison: {winner_reason}")
    parts.append("Educational decision support only — not a diagnosis or prescription.")
    return " ".join(parts)
