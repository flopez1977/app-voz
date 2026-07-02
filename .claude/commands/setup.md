---
description: Instala App-voz (Homebrew, ffmpeg, venv, dependencias, modelo). Idempotente.
---

# Setup App-voz

Install everything needed to run App-voz on this Mac.

## Steps

1. Confirm platform: run `uname -s` and `uname -m`. If not `Darwin` + `arm64`,
   STOP and tell the user this tool is Apple-Silicon only — point them to the
   Windows section of `README.md`. Do not continue.

2. Run the bootstrap:
   ```bash
   bash scripts/bootstrap.sh
   ```

3. If it fails, read the error and fix it interactively with the user:
   - missing Xcode Command Line Tools → `xcode-select --install`
   - Homebrew install prompts → guide the user through them
   - pip/network errors → retry, or check connectivity
   Re-run `bash scripts/bootstrap.sh` after each fix (it is idempotent).

4. When it prints "Bootstrap complete", tell the user:
   - Run `/voz` to set up their voice (or use a default synthetic voice).
   - Run `/tts` to open the dashboard.

Never report success unless bootstrap printed "Bootstrap complete".
