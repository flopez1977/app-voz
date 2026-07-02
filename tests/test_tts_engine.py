import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.tts_engine import speak, resolve_profile


def _make_profile(tmp_path, text="Texto de referencia."):
    prof = tmp_path / "es-test"
    prof.mkdir()
    (prof / "reference.wav").write_bytes(b"RIFFfake")
    (prof / "reference.txt").write_text(text, encoding="utf-8")
    return str(prof)


def test_resolve_profile_dir(tmp_path):
    prof = _make_profile(tmp_path, "Hola ref.")
    wav, ref_text = resolve_profile(prof)
    assert wav.endswith("reference.wav")
    assert ref_text == "Hola ref."


def test_resolve_missing_profile_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve_profile(str(tmp_path / "no-existe"))


def test_dry_run_returns_none_and_generates_nothing(tmp_path):
    prof = _make_profile(tmp_path)
    out_dir = tmp_path / "out"
    result = speak("Hola mundo.", "chunk-01", str(out_dir), prof, dry_run=True)
    assert result is None
    assert not (out_dir / "chunk-01.wav").exists()


def test_idempotent_skip_when_wav_exists(tmp_path):
    prof = _make_profile(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    existing = out_dir / "chunk-01.wav"
    existing.write_bytes(b"RIFFexisting")
    # Should return the existing path without loading the model.
    result = speak("Hola mundo.", "chunk-01", str(out_dir), prof)
    assert result == str(existing)


def test_missing_profile_raises_before_generation(tmp_path):
    with pytest.raises(FileNotFoundError):
        speak("Hola.", "c1", str(tmp_path / "out"), str(tmp_path / "nope"), dry_run=True)
