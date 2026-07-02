import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chunker import chunk_script


def test_returns_voice_chunks_for_paragraphs():
    text = "Primer parrafo.\n\nSegundo parrafo.\n\nTercero."
    chunks = chunk_script(text)
    voice = [c for c in chunks if c["type"] == "voice"]
    assert len(voice) == 3
    assert all("gap_after_ms" in c for c in chunks)


def test_pausa_cue_becomes_silence_chunk():
    text = "Respira hondo.\n\nPAUSA CINCO SEGUNDOS.\n\nAhora suelta."
    chunks = chunk_script(text)
    silences = [c for c in chunks if c["type"] == "silence"]
    assert len(silences) == 1
    assert silences[0]["gap_after_ms"] == 5000
    voice = [c for c in chunks if c["type"] == "voice"]
    assert len(voice) == 2


def test_numeric_pausa():
    chunks = chunk_script("Uno.\n\nPAUSA 3 SEGUNDOS.\n\nDos.")
    silences = [c for c in chunks if c["type"] == "silence"]
    assert silences and silences[0]["gap_after_ms"] == 3000


def test_break_tag_becomes_silence():
    chunks = chunk_script('Hola.\n\n<break time="2s"/>\n\nMundo.')
    silences = [c for c in chunks if c["type"] == "silence"]
    assert silences and silences[0]["gap_after_ms"] == 2000


def test_long_paragraph_splits_at_sentence_boundary():
    long_p = ("Frase una. " * 40).strip()  # ~440 chars, > max_chars
    chunks = chunk_script(long_p, max_chars=280)
    voice = [c for c in chunks if c["type"] == "voice"]
    assert len(voice) >= 2
    assert all(len(c["text"]) <= 280 for c in voice)


def test_voice_text_is_normalized():
    chunks = chunk_script('Hola <break time="1s"/> mundo entero aqui.', )
    # the break is consumed as silence; voice text has no markup
    voice = [c for c in chunks if c["type"] == "voice"]
    assert all("<break" not in c["text"] for c in voice)


def test_replacements_applied_in_voice():
    chunks = chunk_script("El HIIT.", replacements={"HIIT": "interValico"})
    voice = [c for c in chunks if c["type"] == "voice"]
    assert any("interValico" in c["text"] for c in voice)
