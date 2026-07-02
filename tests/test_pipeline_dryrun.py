import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chunker import chunk_script
from engine.tts_engine import speak


def _profile(tmp_path):
    prof = tmp_path / "voz"
    prof.mkdir()
    (prof / "reference.wav").write_bytes(b"RIFFfake")
    (prof / "reference.txt").write_text("Referencia.", encoding="utf-8")
    return str(prof)


def test_end_to_end_dry_run(tmp_path):
    script = (
        '<<<< BLOQUE 1 >>>>\n'
        'Bienvenido. Hoy vamos a empezar <break time="1s"/> con calma.\n\n'
        'PAUSA CINCO SEGUNDOS.\n\n'
        'El HIIT no es magia. Es constancia.'
    )
    chunks = chunk_script(script, replacements={"HIIT": "interValico"})

    # Plan shape: has voice + one silence of 5000ms, markup stripped.
    assert any(c["type"] == "silence" and c["gap_after_ms"] == 5000 for c in chunks)
    voice = [c for c in chunks if c["type"] == "voice"]
    assert voice and all("<break" not in c["text"] and "BLOQUE" not in c["text"] for c in voice)
    assert any("interValico" in c["text"] for c in voice)

    # Dry-run synth of every voice chunk resolves the profile and generates nothing.
    prof = _profile(tmp_path)
    out_dir = tmp_path / "out"
    for i, c in enumerate(voice):
        assert speak(c["text"], f"chunk-{i:03d}", str(out_dir), prof, dry_run=True) is None
    assert not out_dir.exists() or not any(out_dir.iterdir())
