"""
state.py — In-memory job state + SSE listener registry for the dashboard.

Single active job at a time (local, single user). Thread-safe updates; SSE
listeners are notified on every change.
"""

import copy
import threading

_lock = threading.Lock()
_listeners = []

_state = {
    "status": "idle",        # idle | running | done | error
    "phase": "",             # normalize | chunk | synth | assemble
    "progress": 0,           # 0..100
    "total_chunks": 0,
    "done_chunks": 0,
    "chunks": [],            # [{id, type, text, gap_after_ms}]
    "output": None,          # path to final file
    "mode": "voice",
    "error": None,
    "message": "",
}


def get_state():
    with _lock:
        return copy.deepcopy(_state)


def update(partial):
    with _lock:
        _state.update(partial)
        snapshot = copy.deepcopy(_state)
    for cb in list(_listeners):
        try:
            cb(snapshot)
        except Exception:
            pass


def reset():
    update({
        "status": "idle", "phase": "", "progress": 0, "total_chunks": 0,
        "done_chunks": 0, "chunks": [], "output": None, "error": None, "message": "",
    })


def register_sse(callback):
    with _lock:
        _listeners.append(callback)


def unregister_sse(callback):
    with _lock:
        if callback in _listeners:
            _listeners.remove(callback)
