#!/usr/bin/env python3
"""
make_default_voices.py — Generate the two SYNTHETIC default voice profiles.

Run once during packaging (needs mlx-audio, macOS Apple Silicon):

    .venv/bin/python scripts/make_default_voices.py

Uses the Qwen CustomVoice model (built-in synthetic speakers — no real person) to
read the reference script, then saves each result as a voice profile
(reference.wav + reference.txt). The tool's engine later clones these via ICL.

Available CustomVoice speakers:
    serena, vivian, uncle_fu, ryan, aiden, ono_anna, sohee, eric, dylan
"""

import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_TEXT = os.path.join(ROOT, "ref", "guion-referencia.txt")
VOICES = os.path.join(ROOT, "voices")

CUSTOM_VOICE_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"

# name -> built-in speaker preset
DEFAULTS = {
    "es-female": "serena",
    "es-male": "ryan",
}


def main():
    from mlx_audio.tts import load
    from mlx_audio.tts.generate import generate_audio

    model = load(CUSTOM_VOICE_MODEL)

    for name, speaker in DEFAULTS.items():
        out_dir = os.path.join(VOICES, name)
        os.makedirs(out_dir, exist_ok=True)
        generate_audio(
            text=open(REF_TEXT, encoding="utf-8").read().strip(),
            model=model,
            voice=speaker,
            lang_code="es",
            speed=0.95,
            output_path=out_dir,
            file_prefix="reference",
            audio_format="wav",
            save=True,
            join_audio=True,
            verbose=False,
        )
        cand = os.path.join(out_dir, "reference_000.wav")
        final = os.path.join(out_dir, "reference.wav")
        if os.path.exists(cand) and not os.path.exists(final):
            os.rename(cand, final)
        shutil.copy(REF_TEXT, os.path.join(out_dir, "reference.txt"))
        print(f"[ok] {name} ({speaker}): {final}")


if __name__ == "__main__":
    main()
