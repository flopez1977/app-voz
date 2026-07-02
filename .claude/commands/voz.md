---
description: Crea un perfil de voz — grabar o cargar una muestra de referencia.
---

# Voice onboarding

Create a voice profile the TTS engine will clone. A profile is a folder under
`voices/` containing `reference.wav` (mono 24kHz) + `reference.txt` (its exact
transcription).

## First, the consent check

Tell the user: the reference voice must be **their own** or used with explicit
permission. Do not proceed cloning someone else's voice without it.

## Option A — Record (recommended, best quality)

1. Show the fixed reference script:
   ```bash
   cat ref/guion-referencia.txt
   ```
   The user reads THIS text aloud (≥ 20 seconds). Because the text is fixed,
   `reference.txt` is already known — no transcription needed.

2. Ask the user to record themselves reading it (any recorder / QuickTime) and
   give you the file path. Then create the profile (ask for a profile name, e.g.
   `mi-voz`):
   ```bash
   mkdir -p voices/user-<name>
   ffmpeg -y -i "<recording_path>" -ac 1 -ar 24000 voices/user-<name>/reference.wav
   cp ref/guion-referencia.txt voices/user-<name>/reference.txt
   ```

## Option B — Load an existing clip

Same as above, but the transcription must match the clip. If the clip is not the
fixed script, ask the user for its exact transcription and write it to
`reference.txt`. Mismatched text degrades cloning quality.

## Verify

```bash
ffprobe -v error -show_entries stream=channels,sample_rate -of default=noprint_wrappers=1 voices/user-<name>/reference.wav
```
Confirm mono / 24000 Hz. Then tell the user to run `/tts` and pick this profile.
