"""
tts_engine.py — Local TTS via Qwen3-TTS-1.7B on MLX (Apple Silicon) with ICL
voice cloning.

A "voice profile" is a directory containing:
    reference.wav   — mono 24kHz sample of the target voice (>= 20s recommended)
    reference.txt   — exact transcription of reference.wav

speak() is idempotent: if the output .wav already exists it is returned as-is
without loading the model. MLX is imported lazily so the rest of the pipeline
(and the test suite) runs on any platform; actual synthesis requires macOS
Apple Silicon with `mlx` + `mlx-audio` installed.
"""

import os

MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"
LANG = "es"
MAX_CHARS = 500  # safety cap per chunk

_model = None


def resolve_profile(voice_profile):
    """
    Resolve a voice profile to (ref_audio_path, ref_text).

    Accepts a directory containing reference.wav + reference.txt, or a direct
    path to a .wav that has a sibling .txt of the same basename.

    Raises FileNotFoundError if the audio or its transcription is missing.
    """
    if os.path.isdir(voice_profile):
        wav = os.path.join(voice_profile, "reference.wav")
        txt = os.path.join(voice_profile, "reference.txt")
    elif voice_profile.endswith(".wav"):
        wav = voice_profile
        txt = os.path.splitext(voice_profile)[0] + ".txt"
    else:
        raise FileNotFoundError(f"Voice profile not found: {voice_profile}")

    if not os.path.exists(wav):
        raise FileNotFoundError(f"Reference audio not found: {wav}")
    if not os.path.exists(txt):
        raise FileNotFoundError(f"Reference transcription not found: {txt}")

    ref_text = open(txt, encoding="utf-8").read().strip()
    return wav, ref_text


def _get_model():
    global _model
    if _model is None:
        from mlx_audio.tts import load  # lazy: only when actually synthesizing
        _model = load(MODEL_ID)
    return _model


def speak(text, label, output_dir, voice_profile, speed=0.9, dry_run=False):
    """
    Synthesize one chunk. Idempotent (skips if the .wav already exists).

    Args:
        text: text to synthesize.
        label: output filename (without extension).
        output_dir: destination directory.
        voice_profile: path to a voice profile (see resolve_profile).
        speed: speech rate (0.9 validated as a good default).
        dry_run: if True, validate inputs but do not synthesize.

    Returns:
        Path to the .wav, or None on dry_run.
    """
    out_path = os.path.join(output_dir, label + ".wav")

    if os.path.exists(out_path):
        return out_path

    # Validate the profile before any expensive work (also in dry_run).
    ref_audio, ref_text = resolve_profile(voice_profile)

    if dry_run:
        return None

    if len(text) > MAX_CHARS:
        raise ValueError(
            f"Chunk '{label}' too long ({len(text)} > {MAX_CHARS}); chunk first."
        )

    os.makedirs(output_dir, exist_ok=True)
    model = _get_model()

    from mlx_audio.tts.generate import generate_audio
    generate_audio(
        text=text,
        model=model,
        ref_audio=ref_audio,
        ref_text=ref_text,
        output_path=output_dir,
        file_prefix=label,
        audio_format="wav",
        speed=speed,
        lang_code=LANG,
        verbose=False,
        save=True,
        join_audio=True,
    )

    # join_audio=True usually yields {label}.wav; a single short segment may be
    # saved as {label}_000.wav — rename to the canonical path if so.
    candidate = os.path.join(output_dir, label + "_000.wav")
    if not os.path.exists(out_path) and os.path.exists(candidate):
        os.rename(candidate, out_path)

    return out_path
