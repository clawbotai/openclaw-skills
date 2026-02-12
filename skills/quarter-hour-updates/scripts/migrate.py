"""
migrate.py — Daemon-to-Cerebro Migration Script

Handles the clean transition from the legacy `while True` daemon
architecture to the new stateless, scheduled model under Project Cerebro.

Steps:
1. Kill any running daemon process referenced in data/daemon.pid.
2. Patch data/state.json to record the new scheduler.
"""

import json
import os
import signal
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPTS_DIR.parent
_DATA_DIR = _SKILL_DIR / "data"
_PID_FILE = _DATA_DIR / "daemon.pid"
_STATE_FILE = _DATA_DIR / "state.json"

sys.path.insert(0, str(_SCRIPTS_DIR))
from state import load_state, save_state  # noqa: E402


def _kill_daemon() -> bool:
    """Attempt to terminate the legacy daemon process."""

    if not _PID_FILE.exists():
        print("[migrate] No daemon.pid file found — skipping kill step.")
        return False

    try:
        pid_text = _PID_FILE.read_text(encoding="utf-8").strip()
        pid = int(pid_text)
    except (ValueError, OSError) as exc:
        print(f"[migrate] Could not read PID file: {exc}")
        _cleanup_pid_file()
        return False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        print(f"[migrate] PID {pid} is not running — stale PID file.")
        _cleanup_pid_file()
        return False
    except PermissionError:
        print(f"[migrate] PID {pid} exists but permission denied.")
        _cleanup_pid_file()
        return False

    print(f"[migrate] Sending SIGTERM to daemon PID {pid}...")
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"[migrate] SIGTERM sent to PID {pid}.")
    except OSError as exc:
        print(f"[migrate] Failed to send SIGTERM: {exc}")
    finally:
        _cleanup_pid_file()

    return True


def _cleanup_pid_file() -> None:
    try:
        _PID_FILE.unlink(missing_ok=True)
        print("[migrate] Removed daemon.pid.")
    except OSError as exc:
        print(f"[migrate] Warning: could not remove PID file: {exc}")


def _patch_state() -> None:
    state = load_state()
    state["scheduler"] = "cerebro"
    state["status"] = "idle"
    save_state(state)
    print("[migrate] State patched: scheduler set to 'cerebro'.")


def main() -> int:
    print("=" * 60)
    print(" Quarter-Hour Updates — Migration to Project Cerebro")
    print("=" * 60)

    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(" [Step 1/2] Terminating legacy daemon...")
    killed = _kill_daemon()
    if killed:
        print(" -> Daemon terminated.")
    else:
        print(" -> No active daemon to terminate.")

    print(" [Step 2/2] Patching state for Cerebro scheduler...")
    _patch_state()

    print(" Migration complete. Register the Cerebro task with:")
    print(" cerebro register cerebro/tasks/quarter_hour_update.yaml")
    print("=" * 60)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
