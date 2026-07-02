import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.normalizer import normalize


def test_strips_ssml_break():
    assert "<break" not in normalize('Hola <break time="2s"/> mundo.')


def test_strips_pausa_cue():
    out = normalize("Respira. PAUSA DIEZ SEGUNDOS. Sigue.")
    assert "PAUSA" not in out
    assert "Respira." in out and "Sigue." in out


def test_strips_block_and_music_markers():
    out = normalize("<<<< BLOQUE 1 — 1.000 CARACTERES >>>>\n[MÚSICA: ambiental]\nTexto.")
    assert "BLOQUE" not in out
    assert "MÚSICA" not in out
    assert "Texto." in out


def test_applies_replacements():
    out = normalize("El HIIT es duro.", replacements={"HIIT": "entrenamiento interválico"})
    assert "HIIT" not in out
    assert "entrenamiento interválico" in out


def test_strips_uppercase_pronunciation_guide_residue():
    assert "(" not in normalize("Ujjayi (UD-JAYA) respira.")


def test_collapses_multiple_spaces():
    assert "  " not in normalize("Hola     mundo.")


def test_empty_dicts_by_default_no_crash():
    assert normalize("Texto normal sin nada raro.") == "Texto normal sin nada raro."
