"""
normalizer.py — Clean a script before sending it to the TTS engine.

Generic and domain-agnostic. It removes production markup (SSML, cues, block
markers) that should never be read aloud, then applies OPTIONAL user-provided
substitution/pronunciation dictionaries. No domain dictionaries ship by default:
the recipient (or their Claude, via the voz-forge skill) supplies pronunciations
for their own scripts.

Transformations, in order:
1. Strip production markup (SSML <break>, PAUSA cues, block/music/cue markers).
2. Apply pronunciation guides: "Word (GUIDE)" -> phonetic form.
3. Remove leftover "(UPPERCASE)" pronunciation-guide residue.
4. Apply direct replacements (acronyms, foreign terms, name pronunciations).
5. Collapse redundant whitespace.
"""

import re

# Markup that must be removed entirely (never spoken).
STRIP_PATTERNS = [
    # SSML breaks: <break time="2s"/>, <break/>
    re.compile(r'<break\s+time="[^"]*"\s*/>', re.IGNORECASE),
    re.compile(r'<break\s*/>', re.IGNORECASE),
    # Pause cues: "PAUSA DIEZ SEGUNDOS.", "PAUSA 10 SEGUNDOS."
    re.compile(
        r'\bPAUSA\s+(?:DIEZ|VEINTE|TREINTA|CUARENTA|CINCUENTA|SESENTA|'
        r'CINCO|CUATRO|TRES|DOS|UNO?|QUINCE|\d+)\s+SEGUNDOS\.?',
        re.IGNORECASE,
    ),
    # Block markers: <<<< BLOQUE 1 — 1.000 CARACTERES >>>>
    re.compile(r'<{2,}.*?>{2,}', re.DOTALL),
    # Music cues: [MÚSICA: ...]
    re.compile(r'\[M[ÚU]SICA:[^\]]*\]', re.IGNORECASE),
    # Generic production cues in brackets: [pausa Xs], [silencio], [efecto]
    re.compile(r'\[(?:pausa|silencio|m[úu]sica|sonido|efecto)[^\]]*\]', re.IGNORECASE),
    # Arrow annotations and dash placeholders
    re.compile(r'<-+'),
    re.compile(r'——+|--+'),
    # Stray non-latin scripts (e.g. cyrillic) that may have leaked in
    re.compile(r'[а-яА-ЯёЁ]'),
]


def normalize(text, replacements=None, guides=None):
    """
    Normalize a script for TTS.

    Args:
        text: raw script text.
        replacements: optional {original: replacement} applied verbatim.
        guides: optional {"Word (GUIDE)": "phonetic"} pronunciation guides.

    Returns:
        Cleaned text ready for chunking.
    """
    replacements = replacements or {}
    guides = guides or {}

    # 1. Strip production markup.
    for pattern in STRIP_PATTERNS:
        text = pattern.sub('', text)

    # 2. Apply explicit pronunciation guides.
    for original, phonetic in guides.items():
        text = re.sub(re.escape(original), phonetic, text)

    # 3. Remove leftover "(UPPERCASE)" pronunciation-guide residue.
    text = re.sub(r'\s*\([A-ZÁÉÍÓÚÑ\-]+\)', '', text)

    # 4. Direct replacements.
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)

    # 5. Collapse whitespace.
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
