"""
worker.py — Background job runner: script -> chunks -> audio.

Runs a single job in a thread, emitting progress via state.update(). Uses the
engine modules. MLX is only touched when a voice chunk is actually synthesized.
"""

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
