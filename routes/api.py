import base64
import time
import uuid

from flask import Blueprint, jsonify, request, send_file

from config import VOICES, MAX_CHARS
from extensions import limiter
from services.tts import build_params, synthesize

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

_START_TIME = time.time()


def _error(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def _validate_text(data: dict):
    text = data.get("text", "").strip()
    if not text:
        return None, _error("'text' is required and must not be empty")
    if len(text) > MAX_CHARS:
        return None, _error(f"'text' must be {MAX_CHARS} characters or fewer")
    return text, None


# ── Health ──────────────────────────────────────────────────────────────────────

@api_bp.route("/health")
def health():
    return jsonify({
        "ok": True,
        "status": "healthy",
        "uptime_seconds": round(time.time() - _START_TIME),
        "voices_available": len(VOICES),
    })


# ── Voices ──────────────────────────────────────────────────────────────────────

@api_bp.route("/voices")
def list_voices():
    return jsonify({"ok": True, "voices": VOICES})


# ── Synthesize (raw audio) ───────────────────────────────────────────────────────

@api_bp.route("/synthesize", methods=["POST"])
@limiter.limit("30 per minute")
def synthesize_audio():
    """Returns raw audio bytes (MP3 or WAV)."""
    data = request.get_json(silent=True) or {}
    text, err = _validate_text(data)
    if err:
        return err

    voice, rate_str, pitch_str, volume_str, fmt = build_params(data)

    try:
        buf = synthesize(text, voice, rate_str, pitch_str, volume_str)
    except Exception as exc:
        return _error(f"Synthesis failed: {exc}", 500)

    if buf.getbuffer().nbytes == 0:
        return _error("No audio generated — try different text or settings", 500)

    mime = "audio/mpeg" if fmt == "mp3" else "audio/wav"
    return send_file(buf, mimetype=mime, as_attachment=False, download_name=f"speech.{fmt}")


# ── Speak (JSON + base64) ────────────────────────────────────────────────────────

@api_bp.route("/speak", methods=["POST"])
@limiter.limit("30 per minute")
def speak_json():
    """Returns JSON with base64-encoded audio and metadata. Ideal for AI agents."""
    data = request.get_json(silent=True) or {}
    text, err = _validate_text(data)
    if err:
        return err

    voice, rate_str, pitch_str, volume_str, fmt = build_params(data)
    request_id = str(uuid.uuid4())
    t0 = time.time()

    try:
        buf = synthesize(text, voice, rate_str, pitch_str, volume_str)
    except Exception as exc:
        return _error(f"Synthesis failed: {exc}", 500)

    audio_bytes = buf.read()
    if not audio_bytes:
        return _error("No audio generated — try different text or settings", 500)

    voice_info = next((v for v in VOICES if v["id"] == voice), None)
    mime = "audio/mpeg" if fmt == "mp3" else "audio/wav"

    return jsonify({
        "ok": True,
        "request_id": request_id,
        "audio": {
            "base64":    base64.b64encode(audio_bytes).decode("utf-8"),
            "format":    fmt,
            "mime_type": mime,
            "size_bytes": len(audio_bytes),
        },
        "voice": voice_info,
        "settings": {
            "rate":   rate_str,
            "pitch":  pitch_str,
            "volume": volume_str,
        },
        "meta": {
            "text_length":         len(text),
            "generation_seconds":  round(time.time() - t0, 3),
        },
    })
