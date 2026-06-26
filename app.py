import os
import io
import wave
import json
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

MODEL_PATH = "en_US-amy-medium.onnx"
CONFIG_PATH = "en_US-amy-medium.onnx.json"

_voice = None

def get_voice():
    global _voice
    if _voice is None:
        from piper.voice import PiperVoice
        _voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH)
    return _voice

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json()
    text = (data or {}).get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    voice = get_voice()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        voice.synthesize(text, wav_file)
    buf.seek(0)
    return send_file(buf, mimetype="audio/wav", as_attachment=False, download_name="speech.wav")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
