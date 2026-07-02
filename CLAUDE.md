# CLAUDE.md — App-voz

You are operating inside **App-voz**, a local text-to-speech tool that clones the
user's own voice and turns scripts into audio. Everything runs locally on the
user's Mac. You are the installer and operator.

## What this is

A Python pipeline (normalize → chunk → synthesize → assemble) driven by a local
Flask dashboard. TTS is Qwen3-TTS-1.7B via MLX (Apple Silicon). The user records
a short reference of their own voice; the tool clones it.

## Platform requirement

macOS **Apple Silicon (arm64)** only — MLX does not run on Intel or Windows.
If the machine is not arm64 macOS, stop and point the user to the Windows section
of `README.md` (manual swap to an XTTS v2 engine). Do not try to force it.

## Commands

| Command | Purpose |
|---------|---------|
| `/setup` | Install everything (Homebrew, ffmpeg, venv, deps, model). Idempotent. |
| `/voz`   | Create a voice profile — record or load a reference sample. |
| `/tts`   | Start the local dashboard and open it in the browser. |
| `/doctor`| Diagnose the install (arch, brew, ffmpeg, venv, model, voices). |

## Skill

For turning a user's script into a good result, use the **voz-forge** skill
(`.claude/skills/voz-forge/SKILL.md`): it scans the script, proposes
pronunciations for unknown foreign/technical words, and suggests gap placement.
Do not synthesize a whole script without running normalization through it first.

## Rules

1. Never claim the install works without running `/doctor` or a self-test.
2. Voice cloning: the reference voice must belong to the user or be used with
   permission. State this before recording.
3. Keep everything local. This tool has no telemetry, no external calls beyond
   the model download and (optionally) the user's own AI provider.
4. The default voices are synthetic samples for trying the tool — real quality
   comes from the user recording their own voice (script ≥ 20s).

## Layout

```
engine/      normalizer · chunker · tts_engine · assembler   (pure pipeline)
dashboard/   Flask + SSE local webapp
scripts/     bootstrap.sh
voices/      voice profiles (reference.wav + reference.txt)
music/       Pixabay background tracks + user tracks
ref/         guion-referencia.txt  (fixed reference script to read aloud)
```
