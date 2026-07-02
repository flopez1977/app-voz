"""
chunker.py — Split a script into ordered chunks for synthesis.

Produces a flat list of chunk dicts, each one of:
    {"type": "voice",   "text": <str>, "gap_after_ms": <int>}
    {"type": "silence", "text": "",    "gap_after_ms": <int>}

Rules (domain-agnostic):
- Pause cues become silence chunks (their duration), NOT spoken text:
    "PAUSA <N> SEGUNDOS"  (N as Spanish word or digits)
    <break time="Xs"/> / <break time="Xms"/>
- Text is split on blank lines (paragraphs); paragraphs longer than max_chars
  are split at sentence boundaries (. ? !).
- Each voice chunk's text is normalized (markup stripped, optional dicts applied).
"""

import re

from engine.normalizer import normalize

_PAUSE_WORDS = {
    "un": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "diez": 10, "quince": 15, "veinte": 20, "treinta": 30,
    "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
}

# Matches a whole pause cue anywhere in the text.
_PAUSE_RE = re.compile(
    r'\bPAUSA\s+([A-Za-zÁÉÍÓÚáéíóú]+|\d+)\s+SEGUNDOS\.?',
    re.IGNORECASE,
)
_BREAK_RE = re.compile(r'<break\s+time="(\d+)(ms|s)"\s*/>', re.IGNORECASE)


def _pause_ms(token):
    token = token.strip().lower()
    if token.isdigit():
        return int(token) * 1000
    return _PAUSE_WORDS.get(token, 0) * 1000


def _split_paragraph(paragraph, max_chars):
    """Split a paragraph <= max_chars, breaking at sentence boundaries."""
    paragraph = paragraph.strip()
    if len(paragraph) <= max_chars:
        return [paragraph] if paragraph else []

    sentences = re.split(r'(?<=[.?!])\s+', paragraph)
    out, buf = [], ""
    for s in sentences:
        if not buf:
            buf = s
        elif len(buf) + 1 + len(s) <= max_chars:
            buf += " " + s
        else:
            out.append(buf)
            buf = s
    if buf:
        out.append(buf)
    # A single sentence still longer than max_chars: hard-wrap on whitespace.
    final = []
    for piece in out:
        while len(piece) > max_chars:
            cut = piece.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            final.append(piece[:cut].strip())
            piece = piece[cut:].strip()
        if piece:
            final.append(piece)
    return final


def chunk_script(text, max_chars=280, default_gap_ms=1000,
                 replacements=None, guides=None):
    """
    Turn a raw script into an ordered list of voice/silence chunks.

    Args:
        text: raw script.
        max_chars: max characters per voice chunk.
        default_gap_ms: silence appended after each voice chunk.
        replacements / guides: passed to normalize() for each voice chunk.

    Returns:
        list[dict]: ordered chunks.
    """
    # 1. Cut the text at every pause cue, recording the pause durations between.
    tokens = []  # ("text", str) | ("silence", ms)
    pos = 0
    events = []
    for m in _PAUSE_RE.finditer(text):
        events.append((m.start(), m.end(), _pause_ms(m.group(1))))
    for m in _BREAK_RE.finditer(text):
        ms = int(m.group(1)) * (1000 if m.group(2).lower() == "s" else 1)
        events.append((m.start(), m.end(), ms))
    events.sort()

    for start, end, ms in events:
        tokens.append(("text", text[pos:start]))
        tokens.append(("silence", ms))
        pos = end
    tokens.append(("text", text[pos:]))

    # 2. Build chunk list.
    chunks = []
    for kind, val in tokens:
        if kind == "silence":
            if val > 0:
                chunks.append({"type": "silence", "text": "", "gap_after_ms": val})
            continue
        clean = normalize(val, replacements=replacements, guides=guides)
        if not clean:
            continue
        for para in re.split(r'\n\s*\n', clean):
            for piece in _split_paragraph(para, max_chars):
                chunks.append({
                    "type": "voice",
                    "text": piece,
                    "gap_after_ms": default_gap_ms,
                })
    return chunks
