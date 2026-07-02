---
name: voz-forge
description: Use when preparing a script for App-voz synthesis — scan the text, propose pronunciations for foreign/technical/rare words, and suggest silence gaps. Turns a raw script into a clean run config (replacements, pronunciation guides, per-chunk gap overrides) that the engine consumes. Triggers on "prepara este script", "normaliza para voz", "genera la locución", or before any full-script synthesis.
---

# voz-forge — Intelligent normalization for App-voz

The engine's `normalizer.py` only strips markup and applies dictionaries you give
it. Your job is to BUILD those dictionaries per script, and to place the gaps —
this is what makes any script (not just one domain) sound good.

## 1. Scan for pronunciation risks

Read the whole script. Flag words the TTS (Spanish Qwen model) will likely
mispronounce and propose a phonetic Spanish spelling for each:

- Foreign names / brands: `Kobe Bryant → Kobi Braian`, `Djokovic → Yókovich`
- English terms: `flow state → estado de flujo`, `self-talk → diálogo interno`
- Acronyms read letter-by-letter: `HIIT → entrenamiento interválico`, `NBA → N.B.A.`
- Sanskrit / rare words: `Ujjayi → Udyaya`
- Numbers/units that should be spoken in full when ambiguous.

Build a `replacements` dict (`{original: spoken_form}`). For terms written with a
parenthetical guide in the script (`Word (GUIDE)`), add a `guides` entry.

Present the proposed list to the user for a quick confirm before generating —
they know their content. Do not invent pronunciations for names you are unsure
about; ask.

## 2. Place the gaps

The engine puts `default_gap_ms` after every voice chunk. Override where meaning
needs it. Gap rules (validated):

- **Minimum between sentences:** 1000 ms.
- **Calm / meditation content:** 1500–2000 ms.
- **After a question or a dramatic beat:** 2000–3000 ms.
- Explicit pause cues (`PAUSA N SEGUNDOS`, `<break time="Xs"/>`) are already
  honored as silence chunks — keep them.

## 3. Start-of-chunk artifact

The model sometimes clicks on a hard plosive start (P, T, K, B, D, G). When a
chunk starts with one, prefer softening the opening (start on a vowel/soft
consonant if a rewrite is natural) or flag it so the assembler adds a short
pre-silence. Do not change meaning to avoid it.

## 4. Output

Hand the engine/dashboard a run config:

```json
{
  "replacements": { "HIIT": "entrenamiento interválico", "Kobe": "Kobi" },
  "guides":       { "Ujjayi (UD-JAYA)": "Udyaya" },
  "default_gap_ms": 1000,
  "preset": "narration",          // or "meditation" / "podcast"
  "gap_overrides": { "chunk-004": 2500 }
}
```

`normalize(text, replacements, guides)` and `chunk_script(text, ..., replacements,
guides)` consume `replacements`/`guides`. The dashboard applies `gap_overrides`
per chunk before assembly.

## Presets (starting points, then adjust)

| Preset | speed | default gap | notes |
|--------|-------|-------------|-------|
| narration  | 0.95 | 1000 ms | general voiceover |
| meditation | 0.9  | 1800 ms | long calm pauses |
| podcast    | 1.0  | 800 ms  | conversational pace |
