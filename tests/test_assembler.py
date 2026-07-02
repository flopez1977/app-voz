import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.assembler import assemble, generate_silence, get_audio_duration


def test_generate_silence_duration(tmp_path):
    p = tmp_path / "sil.wav"
    generate_silence(500, str(p))
    dur = get_audio_duration(str(p))
    assert abs(dur - 0.5) < 0.1


def test_assemble_voice_only_duration(tmp_path):
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()
    # Two 0.5s stand-in "voice" wavs.
    generate_silence(500, str(chunks_dir / "c0.wav"))
    generate_silence(500, str(chunks_dir / "c1.wav"))

    chunks = [
        {"type": "voice", "id": "c0", "text": "a", "gap_after_ms": 200},
        {"type": "silence", "text": "", "gap_after_ms": 300},
        {"type": "voice", "id": "c1", "text": "b", "gap_after_ms": 0},
    ]
    out_dir = tmp_path / "out"
    result = assemble(chunks, str(chunks_dir), str(out_dir), mode="voice")

    assert os.path.exists(result)
    # 0.5 + 0.2 (gap) + 0.3 (silence) + 0.5 + 0 = 1.5s
    dur = get_audio_duration(result)
    assert abs(dur - 1.5) < 0.4


def test_assemble_missing_chunk_raises(tmp_path):
    chunks = [{"type": "voice", "id": "missing", "text": "x", "gap_after_ms": 0}]
    out_dir = tmp_path / "out"
    try:
        assemble(chunks, str(tmp_path), str(out_dir), mode="voice")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
