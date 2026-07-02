import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "dashboard"))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import app as dashboard_app


def client():
    dashboard_app.app.config["TESTING"] = True
    return dashboard_app.app.test_client()


def test_index_served():
    r = client().get("/")
    assert r.status_code == 200
    assert b"App-voz" in r.data


def test_voices_endpoint_returns_list():
    r = client().get("/api/voices")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_music_endpoint_returns_list():
    r = client().get("/api/music")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_state_endpoint():
    r = client().get("/api/state")
    assert r.status_code == 200
    assert "status" in r.get_json()


def test_normalize_preview():
    r = client().post("/api/normalize-preview", json={"text": 'Hola <break time="1s"/> mundo.'})
    assert r.status_code == 200
    assert "<break" not in r.get_json()["normalized"]


def test_generate_rejects_empty_script():
    r = client().post("/api/generate", json={"script": "", "voice_profile": "x"})
    assert r.status_code == 400


def test_generate_rejects_missing_voice():
    r = client().post("/api/generate", json={"script": "hola", "voice_profile": ""})
    assert r.status_code == 400
