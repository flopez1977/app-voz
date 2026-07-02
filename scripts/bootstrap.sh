#!/usr/bin/env bash
# ============================================================
# App-voz — Bootstrap (idempotent)
# ============================================================
# Prepares a Mac Apple Silicon machine to run App-voz:
#   arch check -> Homebrew -> ffmpeg -> venv -> deps -> model -> self-test
# Re-runnable: skips what is already in place.
#
# Env flags:
#   APPVOZ_SKIP_MODEL=1   skip the model download/warmup (CI / offline)
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
MODEL_ID="mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"

say()  { printf "\033[1;32m▸\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m!\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m✗ %s\033[0m\n" "$*" >&2; exit 1; }

# 1. Platform gate ----------------------------------------------------------
[ "$(uname -s)" = "Darwin" ] || die "App-voz is macOS only. See README for Windows (XTTS v2)."
[ "$(uname -m)" = "arm64" ] || die "App-voz needs Apple Silicon (arm64). MLX does not run on Intel Macs. See README for Windows/Intel alternatives."
say "Apple Silicon macOS detected."

# 2. Homebrew ---------------------------------------------------------------
if ! command -v brew >/dev/null 2>&1; then
  warn "Homebrew not found — installing."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
say "Homebrew present."

# 3. ffmpeg -----------------------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  say "Installing ffmpeg..."
  brew install ffmpeg
fi
say "ffmpeg present: $(command -v ffmpeg)"

# 4. Python venv ------------------------------------------------------------
command -v python3 >/dev/null 2>&1 || die "python3 not found. Install it (brew install python) and re-run."
if [ ! -d "$VENV" ]; then
  say "Creating virtualenv..."
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
say "venv active: $(python --version 2>&1)"

# 5. Dependencies -----------------------------------------------------------
say "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r "$ROOT/requirements.txt"
say "Dependencies installed."

# 6. Model download / warmup ------------------------------------------------
if [ "${APPVOZ_SKIP_MODEL:-0}" = "1" ]; then
  warn "APPVOZ_SKIP_MODEL=1 — skipping model download."
else
  say "Downloading / caching model (~500MB, first run only)..."
  python - <<PY
from mlx_audio.tts import load
load("${MODEL_ID}")
print("model ready")
PY
fi

# 7. Self-test --------------------------------------------------------------
DEFAULT_VOICE="$ROOT/voices/es-female"
if [ "${APPVOZ_SKIP_MODEL:-0}" != "1" ] && [ -f "$DEFAULT_VOICE/reference.wav" ]; then
  say "Self-test: synthesizing a short sample..."
  python - <<PY
import sys
sys.path.insert(0, "${ROOT}")
from engine.tts_engine import speak
out = speak("Hola, esto es una prueba.", "selftest", "${ROOT}/output", "${DEFAULT_VOICE}")
print("self-test wav:", out)
PY
  say "Self-test OK."
else
  warn "Self-test skipped (no default voice yet or model skipped)."
fi

say "Bootstrap complete. Run /tts to open the dashboard."
