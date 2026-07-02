---
description: Arranca el dashboard local de App-voz y lo abre en el navegador.
---

# Open the dashboard

Start the local App-voz webapp and open it.

## Steps

1. Make sure setup ran (the `.venv` exists). If not, tell the user to run `/setup` first.

2. Start the dashboard in the background:
   ```bash
   .venv/bin/python dashboard/app.py
   ```
   It serves on http://localhost:5050.

3. Open it:
   ```bash
   open http://localhost:5050
   ```

4. Tell the user the dashboard is running at http://localhost:5050 and how to
   stop it (Ctrl-C in the terminal / close the process). Point out the flow:
   pick a voice → paste/upload a script → review the normalized preview → generate
   → review chunks and gaps → export (voice only or voice + music).

If port 5050 is busy, start with `APPVOZ_PORT=<port> .venv/bin/python dashboard/app.py`
and open that port instead.
