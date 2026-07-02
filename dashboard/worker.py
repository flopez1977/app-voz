"""
worker.py — Background job runner: script -> chunks -> audio.

Runs a single job in a thread, emitting progress via state.update(). Uses the
engine modules. MLX is only touched when a voice chunk is actually synthesized.
"""

import json
import os
import threading

import state as st
from engine.chunker import chunk_script
from engine.tts_engine import speak
from engine.assembler import assemble

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "output")
CHUNKS_DIR = os.path.join(OUTPUT_DIR, "chunks")

_thread = None


def _manifest_path(chunks_dir):
    return os.path.join(chunks_dir, "manifest.json")


def _load_manifest(chunks_dir):
    try:
        with open(_manifest_path(chunks_dir), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sync_chunk_cache(chunks, chunks_dir):
    """
    Keep the chunk-audio cache consistent with the current script.

    Deletes cached wavs whose text changed (so they are re-synthesized) and
    orphan wavs whose label is no longer in the plan. Returns the current
    {label: text} map. Chunks whose text is unchanged keep their wav, so a
    gap-only re-assemble stays fast (speak() skips them).
    """
    manifest = _load_manifest(chunks_dir)
    current = {c["id"]: c["text"] for c in chunks if c["type"] == "voice"}
    for label, text in current.items():
        if manifest.get(label) != text:
            wav = os.path.join(chunks_dir, label + ".wav")
            if os.path.exists(wav):
                os.remove(wav)
    if os.path.isdir(chunks_dir):
        for f in os.listdir(chunks_dir):
            if f.startswith("chunk-") and f.endswith(".wav") and f[:-4] not in current:
                os.remove(os.path.join(chunks_dir, f))
    return current


def _save_manifest(chunks_dir, current):
    os.makedirs(chunks_dir, exist_ok=True)
    with open(_manifest_path(chunks_dir), "w", encoding="utf-8") as f:
        json.dump(current, f)


def _run(job):
    try:
        st.reset()
        st.update({"status": "running", "phase": "chunk", "message": "Troceando script..."})

        chunks = chunk_script(
            job["script"],
            max_chars=job.get("max_chars", 280),
            default_gap_ms=job.get("default_gap_ms", 1000),
            replacements=job.get("replacements") or {},
            guides=job.get("guides") or {},
        )

        # Assign stable ids + apply per-chunk gap overrides.
        overrides = job.get("gap_overrides") or {}
        for i, c in enumerate(chunks):
            c["id"] = f"chunk-{i:03d}"
            if c["id"] in overrides:
                c["gap_after_ms"] = int(overrides[c["id"]])

        voice_chunks = [c for c in chunks if c["type"] == "voice"]
        st.update({
            "chunks": chunks,
            "total_chunks": len(voice_chunks),
            "done_chunks": 0,
            "phase": "synth",
            "message": "Generando voz...",
        })

        os.makedirs(CHUNKS_DIR, exist_ok=True)
        # Drop cached wavs whose text changed (stale) or whose label is gone.
        current = sync_chunk_cache(chunks, CHUNKS_DIR)
        profile = job["voice_profile"]
        speed = job.get("speed", 0.9)

        done = 0
        for c in chunks:
            if c["type"] != "voice":
                continue
            speak(c["text"], c["id"], CHUNKS_DIR, profile, speed=speed)
            done += 1
            st.update({
                "done_chunks": done,
                "progress": int(done / max(len(voice_chunks), 1) * 90),
                "message": f"Chunk {done}/{len(voice_chunks)}",
            })
        _save_manifest(CHUNKS_DIR, current)

        st.update({"phase": "assemble", "message": "Ensamblando audio..."})
        mode = job.get("mode", "voice")
        music = job.get("music_path")
        output = assemble(chunks, CHUNKS_DIR, OUTPUT_DIR, music_path=music, mode=mode)

        st.update({
            "status": "done", "phase": "", "progress": 100,
            "output": output, "mode": mode, "message": "Listo.",
        })
    except Exception as e:  # surface any failure to the UI
        st.update({"status": "error", "error": str(e), "message": f"Error: {e}"})


def start_job(job):
    """Start a generation job in the background. Returns False if one is running."""
    global _thread
    if _thread and _thread.is_alive():
        return False
    _thread = threading.Thread(target=_run, args=(job,), daemon=True)
    _thread.start()
    return True


def is_running():
    return bool(_thread and _thread.is_alive())
