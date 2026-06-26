import io
import wave
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
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        length_scale = float(data.get("speed", 1.0))
        noise_scale = float(data.get("expressiveness", 0.667))
        noise_w_scale = float(data.get("variation", 0.8))
        volume = float(data.get("volume", 1.0))

        length_scale = max(0.25, min(4.0, length_scale))
        noise_scale = max(0.0, min(2.0, noise_scale))
        noise_w_scale = max(0.0, min(2.0, noise_w_scale))
        volume = max(0.1, min(2.0, volume))

        from piper.config import SynthesisConfig
        syn_config = SynthesisConfig(
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_w_scale=noise_w_scale,
            volume=volume,
        )

        voice = get_voice()
        all_bytes = b""
        sample_rate = 22050
        sample_width = 2
        sample_channels = 1

        for chunk in voice.synthesize(text, syn_config=syn_config):
            all_bytes += chunk.audio_int16_bytes
            sample_rate = chunk.sample_rate
            sample_width = chunk.sample_width
            sample_channels = chunk.sample_channels

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(sample_channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(all_bytes)

        buf.seek(0)
        return send_file(buf, mimetype="audio/wav", as_attachment=False, download_name="speech.wav")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
