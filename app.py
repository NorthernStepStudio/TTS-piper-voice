import asyncio
import base64
import io
import os
import time
import uuid

import edge_tts
from flask import Flask, jsonify, render_template, request, send_file, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per hour", "20 per minute"],
    storage_uri="memory://",
)

VOICES = [
    {"id": "en-US-AvaNeural",         "name": "Ava",         "gender": "Female", "style": "Natural, warm"},
    {"id": "en-US-EmmaNeural",        "name": "Emma",        "gender": "Female", "style": "Natural, friendly"},
    {"id": "en-US-JennyNeural",       "name": "Jenny",       "gender": "Female", "style": "Conversational"},
    {"id": "en-US-AriaNeural",        "name": "Aria",        "gender": "Female", "style": "Expressive"},
    {"id": "en-US-MichelleNeural",    "name": "Michelle",    "gender": "Female", "style": "Clear, professional"},
    {"id": "en-US-AndrewNeural",      "name": "Andrew",      "gender": "Male",   "style": "Natural, warm"},
    {"id": "en-US-BrianNeural",       "name": "Brian",       "gender": "Male",   "style": "Natural, friendly"},
    {"id": "en-US-ChristopherNeural", "name": "Christopher", "gender": "Male",   "style": "Deep, professional"},
    {"id": "en-US-EricNeural",        "name": "Eric",        "gender": "Male",   "style": "Clear, confident"},
    {"id": "en-US-GuyNeural",         "name": "Guy",         "gender": "Male",   "style": "Expressive"},
    {"id": "en-US-RogerNeural",       "name": "Roger",       "gender": "Male",   "style": "Calm, articulate"},
]

VALID_IDS = {v["id"] for v in VOICES}
VALID_FORMATS = {"mp3", "wav"}

_START_TIME = time.time()


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


async def _synthesize_async(text, voice, rate_str, pitch_str, volume_str):
    communicate = edge_tts.Communicate(
        text, voice=voice, rate=rate_str, pitch=pitch_str, volume=volume_str
    )
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf


def _build_params(data):
    voice = data.get("voice", "en-US-AvaNeural")
    if voice not in VALID_IDS:
        voice = "en-US-AvaNeural"
    rate   = _clamp(int(data.get("rate",   0)), -50, 100)
    pitch  = _clamp(int(data.get("pitch",  0)), -20,  20)
    volume = _clamp(int(data.get("volume", 0)), -50,  50)
    fmt    = data.get("format", "mp3").lower()
    if fmt not in VALID_FORMATS:
        fmt = "mp3"
    return voice, f"{rate:+d}%", f"{pitch:+d}Hz", f"{volume:+d}%", fmt


def _error(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


# ── UI routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    base_url = request.host_url.rstrip("/")
    return render_template("index.html", voices=VOICES, base_url=base_url)


# ── API v1 ─────────────────────────────────────────────────────────────────────

@app.route("/api/v1/health")
def health():
    return jsonify({
        "ok": True,
        "status": "healthy",
        "uptime_seconds": round(time.time() - _START_TIME),
        "voices_available": len(VOICES),
    })


@app.route("/api/v1/voices")
def list_voices():
    return jsonify({"ok": True, "voices": VOICES})


@app.route("/api/v1/synthesize", methods=["POST"])
@limiter.limit("30 per minute")
def synthesize_audio():
    """Returns raw audio bytes (MP3 or WAV)."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return _error("'text' is required and must not be empty")
    if len(text) > 5000:
        return _error("'text' must be 5000 characters or fewer")

    voice, rate_str, pitch_str, volume_str, fmt = _build_params(data)

    try:
        buf = asyncio.run(_synthesize_async(text, voice, rate_str, pitch_str, volume_str))
    except Exception as e:
        return _error(f"Synthesis failed: {e}", 500)

    if buf.getbuffer().nbytes == 0:
        return _error("No audio generated — try different text or settings", 500)

    mime = "audio/mpeg" if fmt == "mp3" else "audio/wav"
    filename = f"speech.{fmt}"
    return send_file(buf, mimetype=mime, as_attachment=False, download_name=filename)


@app.route("/api/v1/speak", methods=["POST"])
@limiter.limit("30 per minute")
def speak_json():
    """Returns JSON with base64-encoded audio, voice info, and metadata.
    Ideal for AI agents and programmatic consumers."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return _error("'text' is required and must not be empty")
    if len(text) > 5000:
        return _error("'text' must be 5000 characters or fewer")

    voice, rate_str, pitch_str, volume_str, fmt = _build_params(data)
    request_id = str(uuid.uuid4())
    t0 = time.time()

    try:
        buf = asyncio.run(_synthesize_async(text, voice, rate_str, pitch_str, volume_str))
    except Exception as e:
        return _error(f"Synthesis failed: {e}", 500)

    audio_bytes = buf.read()
    if not audio_bytes:
        return _error("No audio generated — try different text or settings", 500)

    elapsed = round(time.time() - t0, 3)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    voice_info = next((v for v in VOICES if v["id"] == voice), None)

    return jsonify({
        "ok": True,
        "request_id": request_id,
        "audio": {
            "base64": audio_b64,
            "format": fmt,
            "mime_type": "audio/mpeg" if fmt == "mp3" else "audio/wav",
            "size_bytes": len(audio_bytes),
        },
        "voice": voice_info,
        "settings": {
            "rate": rate_str,
            "pitch": pitch_str,
            "volume": volume_str,
        },
        "meta": {
            "text_length": len(text),
            "generation_seconds": elapsed,
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
