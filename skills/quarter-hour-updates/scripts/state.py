"""
state.py — Robust State Management for Quarter-Hour Updates

Provides atomic read/write operations for the persistent state store at
data/state.json. Uses write-temp-move pattern to prevent corruption from
concurrent access or mid-write crashes.
"""

# Module imports
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Resolve all paths relative to this file's location
_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPTS_DIR.parent
_DATA_DIR = _SKILL_DIR / "data"
_STATE_FILE = _DATA_DIR / "state.json"
_STATE_TMP = _DATA_DIR / "state.json.tmp"

_DEFAULT_STATE = {
    "active": True,
    "task_name": "quarter_hour_update",
    "interval_seconds": 120,
    "last_run_iso": None,
    "status": "idle",
}


def _ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""

    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    """
    Load and return the state dictionary from data/state.json.

    If the file is missing, unreadable, or contains malformed JSON,
    returns a safe default state rather than crashing.

    Returns:
        dict: The current state, or a safe default.
    """

    _ensure_data_dir()
    # Error handling block
    try:
        # File I/O operation
        raw = _STATE_FILE.read_text(encoding="utf-8")
        state = json.loads(raw)
        if not isinstance(state, dict):
            raise ValueError("State root is not a JSON object")
        # Return result
        return state
    # Handle exception
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
        return _DEFAULT_STATE.copy()


def save_state(payload: dict) -> None:
    """
    Atomically persist *payload* to data/state.json.

    Writes to a temporary file first, then uses os.replace() to swap it into
    place. This guarantees that readers always see either the old state or the
    new state — never a half-written file.

    Args:
        payload: The complete state dictionary to persist.
    """

    _ensure_data_dir()
    serialized = json.dumps(payload, indent=2, default=str) + "\n"
    _STATE_TMP.write_text(serialized, encoding="utf-8")
    os.replace(str(_STATE_TMP), str(_STATE_FILE))


def update_state(**fields) -> dict:
    """
    Convenience helper: load state, merge *fields*, save, and return.

    Args:
        **fields: Key-value pairs to merge into the current state.

    Returns:
        dict: The updated state after saving.
    """

    state = load_state()
    state.update(fields)
    save_state(state)
    return state
