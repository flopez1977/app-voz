"""
app.py — App-voz local dashboard (Flask + SSE).

Run: .venv/bin/python dashboard/app.py   → http://localhost:5050
"""

import json
import os
import queue
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)                              # so `engine` package imports
sys.path.insert(0, os.path.join(ROOT, "dashboard"))  # so `state` / `worker` import

from flask import Flask, Response, jsonify, request, send_file, send_from_directory

import state as st
import worker
from engine.normalizer import normalize

VOICES_DIR = os.path.join(ROOT, "voices")
MUSIC_DIR = os.path.join(ROOT, "music")
REF_SCRIPT = os.path.join(ROOT, "ref", "guion-referencia.txt")
OUTPUT_DIR = os.path.join(ROOT, "output")
CHUNKS_DIR = os.path.join(OUTPUT_DIR, "chunks")

app = Flask(__name__, static_folder=os.path.join(ROOT, "dashboard", "static"))


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/voices")
def api_voices():
    voices = []
    if os.path.isdir(VOICES_DIR):
        for name in sorted(os.listdir(VOICES_DIR)):
            d = os.path.join(VOICES_DIR, name)
            if os.path.isdir(d) and os.path.exists(os.path.join(d, "reference.wav")):
                voices.append(name)
    return jsonify(voices)


@app.route("/api/music")
def api_music():
    tracks = []
    if os.path.isdir(MUSIC_DIR):
        for name in sorted(os.listdir(MUSIC_DIR)):
            if name.lower().endswith((".mp3", ".wav", ".m4a", ".ogg")):
                tracks.append(name)
    return jsonify(tracks)


@app.route("/api/reference-script")
def api_reference_script():
    if os.path.exists(REF_SCRIPT):
        return jsonify({"text": open(REF_SCRIPT, encoding="utf-8").read()})
    return jsonify({"text": ""})


@app.route("/api/normalize-preview", methods=["POST"])
def api_normalize_preview():
    data = request.get_json(force=True)
    normalized = normalize(
        data.get("text", ""),
        replacements=data.get("replacements") or {},
        guides=data.get("guides") or {},
    )
    return jsonify({"normalized": normalized})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    if worker.is_running():
        return jsonify({"ok": False, "error": "Ya hay un trabajo en curso."}), 409
    data = request.get_json(force=True)
    if not data.get("script", "").strip():
        return jsonify({"ok": False, "error": "Script vacío."}), 400
    if not data.get("voice_profile"):
        return jsonify({"ok": False, "error": "Falta la voz."}), 400

    profile = os.path.join(VOICES_DIR, data["voice_profile"])
    music_path = None
    if data.get("mode") == "voice_music" and data.get("music"):
        music_path = os.path.join(MUSIC_DIR, data["music"])

    job = {
        "script": data["script"],
        "voice_profile": profile,
        "speed": float(data.get("speed", 0.9)),
        "mode": data.get("mode", "voice"),
        "music_path": music_path,
        "default_gap_ms": int(data.get("default_gap_ms", 1000)),
        "replacements": data.get("replacements") or {},
        "guides": data.get("guides") or {},
        "gap_overrides": data.get("gap_overrides") or {},
    }
    worker.start_job(job)
    return jsonify({"ok": True})


@app.route("/api/state")
def api_state():
    return jsonify(st.get_state())


@app.route("/api/chunk-audio/<label>")
def api_chunk_audio(label):
    path = os.path.join(CHUNKS_DIR, os.path.basename(label) + ".wav")
    if os.path.exists(path):
        return send_file(path, mimetype="audio/wav")
    return ("not found", 404)


@app.route("/api/output-audio")
def api_output_audio():
    s = st.get_state()
    if s.get("output") and os.path.exists(s["output"]):
        return send_file(s["output"], mimetype="audio/wav")
    return ("not found", 404)


@app.route("/api/download")
def api_download():
    s = st.get_state()
    if s.get("output") and os.path.exists(s["output"]):
        return send_file(s["output"], as_attachment=True,
                         download_name=os.path.basename(s["output"]))
    return ("not found", 404)


@app.route("/events")
def events():
    def stream():
        q = queue.Queue(maxsize=50)
        st.register_sse(lambda s: q.put_nowait(s) if not q.full() else None)
        try:
            yield f"data: {json.dumps(st.get_state())}\n\n"
            while True:
                try:
                    s = q.get(timeout=25)
                    yield f"data: {json.dumps(s)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            return
    return Response(stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    port = int(os.environ.get("APPVOZ_PORT", "5050"))
    app.run(host="127.0.0.1", port=port, threaded=True)
