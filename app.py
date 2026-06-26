import io
import asyncio
import edge_tts
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

VOICES = [
    {"id": "en-US-AvaNeural",        "name": "Ava",         "gender": "Female", "style": "Natural, warm"},
    {"id": "en-US-EmmaNeural",       "name": "Emma",        "gender": "Female", "style": "Natural, friendly"},
    {"id": "en-US-JennyNeural",      "name": "Jenny",       "gender": "Female", "style": "Conversational"},
    {"id": "en-US-AriaNeural",       "name": "Aria",        "gender": "Female", "style": "Expressive"},
    {"id": "en-US-MichelleNeural",   "name": "Michelle",    "gender": "Female", "style": "Clear, professional"},
    {"id": "en-US-AndrewNeural",     "name": "Andrew",      "gender": "Male",   "style": "Natural, warm"},
    {"id": "en-US-BrianNeural",      "name": "Brian",       "gender": "Male",   "style": "Natural, friendly"},
    {"id": "en-US-ChristopherNeural","name": "Christopher", "gender": "Male",   "style": "Deep, professional"},
    {"id": "en-US-EricNeural",       "name": "Eric",        "gender": "Male",   "style": "Clear, confident"},
    {"id": "en-US-GuyNeural",        "name": "Guy",         "gender": "Male",   "style": "Expressive"},
    {"id": "en-US-RogerNeural",      "name": "Roger",       "gender": "Male",   "style": "Calm, articulate"},
]

@app.route("/")
def index():
    return render_template("index.html", voices=VOICES)

@app.route("/voices")
def get_voices():
    return jsonify(VOICES)

@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    voice_id = data.get("voice", "en-US-AvaNeural")
    valid_ids = {v["id"] for v in VOICES}
    if voice_id not in valid_ids:
        voice_id = "en-US-AvaNeural"

    try:
        rate = int(data.get("rate", 0))
        rate = max(-50, min(100, rate))
        pitch = int(data.get("pitch", 0))
        pitch = max(-20, min(20, pitch))
        volume = int(data.get("volume", 0))
        volume = max(-50, min(50, volume))

        rate_str   = f"{rate:+d}%"
        pitch_str  = f"{pitch:+d}Hz"
        volume_str = f"{volume:+d}%"

        async def do_synth():
            communicate = edge_tts.Communicate(
                text,
                voice=voice_id,
                rate=rate_str,
                pitch=pitch_str,
                volume=volume_str,
            )
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            buf.seek(0)
            return buf

        buf = asyncio.run(do_synth())

        if buf.getbuffer().nbytes == 0:
            return jsonify({"error": "No audio generated — try different text or settings"}), 500

        return send_file(buf, mimetype="audio/mpeg", as_attachment=False, download_name="speech.mp3")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
