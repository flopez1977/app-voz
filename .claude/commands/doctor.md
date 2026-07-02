---
description: Diagnostica la instalación de App-voz.
---

# Doctor

Check the App-voz install and report what is OK and what is missing. Run these
and summarize results in a table (OK / MISSING + fix):

```bash
echo "arch:   $(uname -s) $(uname -m)   (need Darwin arm64)"
echo "brew:   $(command -v brew || echo MISSING)"
echo "ffmpeg: $(command -v ffmpeg || echo MISSING)"
echo "venv:   $([ -d .venv ] && echo present || echo MISSING)"
[ -d .venv ] && .venv/bin/python -c "import mlx, mlx_audio, flask; print('deps: OK')" 2>&1 || echo "deps: MISSING (run /setup)"
ls ~/.cache/huggingface/hub/ 2>/dev/null | grep -i qwen3-tts || echo "model: NOT cached (run /setup)"
echo "voices:"; ls -1 voices/ 2>/dev/null || echo "  none (run /voz)"
```

For each MISSING item, give the one-line fix (usually: run `/setup`, or `/voz`
for voices). If everything is OK, tell the user to run `/tts`.
