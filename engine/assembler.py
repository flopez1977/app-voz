"""
assembler.py — Concatenate synthesized chunks into a final track.

Two modes:
    "voice"        → narration only (chunks + gaps + silences), loudnorm + fades.
    "voice_music"  → narration mixed under an optional background track with
                     fade in/out (music looped/trimmed to fit).

No heartbeat. Requires ffmpeg/ffprobe on PATH.
"""

import os
import subprocess
import tempfile


def get_audio_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def generate_silence(duration_ms, output_path, sample_rate=44100):
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r={sample_rate}:cl=stereo",
        "-t", str(duration_ms / 1000),
        "-acodec", "pcm_s16le", output_path,
    ], check=True, capture_output=True)


def normalize_wav(input_path, output_path, sample_rate=44100,
                  fadein_ms=35, fadeout_ms=25, loudnorm=True):
    """Convert to stereo 44.1kHz, optional loudnorm (EBU R128), fade in/out."""
    dur = get_audio_duration(input_path)
    fadeout_start = max(dur - fadeout_ms / 1000, 0)
    loud = "loudnorm=I=-16:TP=-1.5:LRA=11," if loudnorm else ""
    af = (
        f"{loud}"
        f"afade=t=in:st=0:d={fadein_ms/1000},"
        f"afade=t=out:st={fadeout_start:.4f}:d={fadeout_ms/1000}"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path, "-af", af,
        "-ar", str(sample_rate), "-ac", "2", "-acodec", "pcm_s16le", output_path,
    ], check=True, capture_output=True)


def _concat(parts, output_path):
    inputs = []
    for p in parts:
        inputs += ["-i", p]
    filt = "".join(f"[{i}:a]" for i in range(len(parts)))
    filt += f"concat=n={len(parts)}:v=0:a=1[out]"
    subprocess.run([
        "ffmpeg", "-y", *inputs, "-filter_complex", filt,
        "-map", "[out]", "-acodec", "pcm_s16le", "-ar", "44100", output_path,
    ], check=True, capture_output=True)


def _build_narration(chunks, chunks_dir, tmp):
    """Normalize voice chunks, insert gaps and silence chunks; return part paths."""
    parts = []
    for i, chunk in enumerate(chunks):
        if chunk["type"] == "silence":
            gap = chunk.get("gap_after_ms", 0)
            if gap > 0:
                sp = os.path.join(tmp, f"sil_{i}.wav")
                generate_silence(gap, sp)
                parts.append(sp)
            continue

        label = chunk.get("id") or f"chunk-{i:03d}"
        chunk_path = os.path.join(chunks_dir, label + ".wav")
        if not os.path.exists(chunk_path):
            raise FileNotFoundError(f"Chunk audio not found: {chunk_path}")

        norm = os.path.join(tmp, f"norm_{i}.wav")
        normalize_wav(chunk_path, norm, loudnorm=True)
        parts.append(norm)

        gap = chunk.get("gap_after_ms", 0)
        if gap > 0:
            sp = os.path.join(tmp, f"gap_{i}.wav")
            generate_silence(gap, sp)
            parts.append(sp)
    return parts


def _mix_music(narration_path, music_path, output_path, config):
    """Mix narration over a background track with fades; loop/trim music to fit."""
    total = get_audio_duration(narration_path)
    vol_db = config.get("music_volume_db", -18)
    fadein = config.get("music_fadein_s", 3)
    fadeout = config.get("music_fadeout_s", 8)
    vol = 10 ** (vol_db / 20)

    with tempfile.TemporaryDirectory() as tmp:
        norm_music = os.path.join(tmp, "music_norm.wav")
        normalize_wav(music_path, norm_music, loudnorm=False)
        mdur = get_audio_duration(norm_music)

        if mdur < total:
            loops = int(total / mdur) + 2
            looped = os.path.join(tmp, "music_loop.wav")
            _concat([norm_music] * loops, looped)
            music = looped
        else:
            music = norm_music

        fadeout_start = max(total - fadeout, 0)
        filt = (
            f"[1:a]volume={vol:.4f},"
            f"afade=t=in:st=0:d={fadein},"
            f"afade=t=out:st={fadeout_start:.2f}:d={fadeout}[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", narration_path, "-i", music,
            "-filter_complex", filt, "-map", "[out]",
            "-acodec", "pcm_s16le", "-ar", "44100", output_path,
        ], check=True, capture_output=True)


def assemble(chunks, chunks_dir, output_dir, music_path=None, mode="voice", config=None):
    """
    Assemble chunks into a final wav.

    Args:
        chunks: ordered chunk dicts (voice chunks need matching <id>.wav files).
        chunks_dir: directory holding the per-chunk voice wavs.
        output_dir: where the result is written.
        music_path: background track (required for mode="voice_music").
        mode: "voice" or "voice_music".
        config: optional music mix overrides.

    Returns:
        Path to the produced wav.
    """
    config = config or {}
    os.makedirs(output_dir, exist_ok=True)
    narration_out = os.path.join(output_dir, "narration.wav")

    with tempfile.TemporaryDirectory() as tmp:
        parts = _build_narration(chunks, chunks_dir, tmp)
        if not parts:
            raise ValueError("No chunks to assemble.")
        _concat(parts, narration_out)

    if mode == "voice_music":
        if not music_path or not os.path.exists(music_path):
            raise FileNotFoundError(f"Music track required for voice_music: {music_path}")
        final_out = os.path.join(output_dir, "narration_music.wav")
        _mix_music(narration_out, music_path, final_out, config)
        return final_out

    return narration_out
