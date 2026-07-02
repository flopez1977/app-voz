import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "dashboard"))

import worker


def _wav(p):
    open(p, "wb").write(b"RIFFxxxx")


def test_sync_removes_changed_and_orphan_keeps_same(tmp_path):
    cdir = tmp_path / "chunks"
    cdir.mkdir()
    _wav(str(cdir / "chunk-000.wav"))   # text will change -> remove
    _wav(str(cdir / "chunk-001.wav"))   # text same -> keep
    _wav(str(cdir / "chunk-009.wav"))   # orphan -> remove
    (cdir / "manifest.json").write_text(json.dumps({
        "chunk-000": "viejo", "chunk-001": "igual", "chunk-009": "fuera",
    }))

    chunks = [
        {"type": "voice", "id": "chunk-000", "text": "nuevo", "gap_after_ms": 0},
        {"type": "voice", "id": "chunk-001", "text": "igual", "gap_after_ms": 0},
    ]
    current = worker.sync_chunk_cache(chunks, str(cdir))

    assert not (cdir / "chunk-000.wav").exists()   # changed -> regenerated
    assert (cdir / "chunk-001.wav").exists()        # unchanged -> kept
    assert not (cdir / "chunk-009.wav").exists()    # orphan -> removed
    assert current == {"chunk-000": "nuevo", "chunk-001": "igual"}
