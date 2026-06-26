import io
import wave
import struct
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
        all_samples = []
        sample_rate = None

        for chunk in voice.synthesize(text, syn_config=syn_config):
            all_samples.extend(chunk.audio)
            if sample_rate is None:
                sample_rate = chunk.sample_rate

        if sample_rate is None:
            sample_rate = 22050

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f"<{len(all_samples)}h", *all_samples))

        buf.seek(0)
        return send_file(buf, mimetype="audio/wav", as_attachment=False, download_name="speech.wav")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
