import asyncio
import io

import edge_tts

from config import DEFAULT_VOICE, DEFAULT_FORMAT, VALID_VOICE_IDS, VALID_FORMATS, MAX_CHARS


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def build_params(data: dict) -> tuple:
    """Validate and normalize synthesis parameters from a request dict."""
    voice = data.get("voice", DEFAULT_VOICE)
    if voice not in VALID_VOICE_IDS:
        voice = DEFAULT_VOICE

    rate   = _clamp(int(data.get("rate",   0)), -50, 100)
    pitch  = _clamp(int(data.get("pitch",  0)), -20,  20)
    volume = _clamp(int(data.get("volume", 0)), -50,  50)

    fmt = data.get("format", DEFAULT_FORMAT).lower()
    if fmt not in VALID_FORMATS:
        fmt = DEFAULT_FORMAT

    return voice, f"{rate:+d}%", f"{pitch:+d}Hz", f"{volume:+d}%", fmt


async def _run(text: str, voice: str, rate: str, pitch: str, volume: str) -> io.BytesIO:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, volume=volume)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf


def synthesize(text: str, voice: str, rate: str, pitch: str, volume: str) -> io.BytesIO:
    """Synthesize text to speech and return a BytesIO buffer of MP3 data."""
    return asyncio.run(_run(text, voice, rate, pitch, volume))
