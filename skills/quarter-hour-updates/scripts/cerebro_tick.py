"""
cerebro_tick.py — The One-Shot Executor for Quarter-Hour Updates

This is the entry point that Project Cerebro invokes on schedule. It
performs exactly one atomic update cycle and exits.

Exit codes:
    0 — Success, or gracefully skipped (active=False).
    1 — An error occurred (details logged to observability.jsonl).
"""

# Module imports
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution — all paths relative to *this file*
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPTS_DIR.parent
_DATA_DIR = _SKILL_DIR / "data"
_OBSERVABILITY_LOG = _DATA_DIR / "observability.jsonl"
_PROGRESS_FILE = _SKILL_DIR.parent.parent / "progress.md"

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(_SCRIPTS_DIR))
from state import load_state, save_state  # noqa: E402
from log_progress import generate_payload  # noqa: E402


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""

    # Return result
    return datetime.now(timezone.utc).isoformat()


def _hash_text(text: str) -> str:
    """Return a short hex digest of *text* for observability deduplication."""

    # Return result
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def _append_observability(record: dict) -> None:
    """Append a single JSON record to data/observability.jsonl."""

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, default=str) + "\n"
    with _OBSERVABILITY_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)


def _append_progress(timestamp: str, synopsis: str, next_steps: list[str]) -> None:
    """Append a formatted markdown update block to progress.md."""

    _PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    steps_md = "\n".join(f"- {step}" for step in next_steps)
    block = (
        f"\n### Quarter-Hour Update — {timestamp}\n"
        f"Synopsis: {synopsis}\n"
        f"Next steps:\n{steps_md}\n"
    )
    with _PROGRESS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(block)


def main() -> int:
    """Execute one complete update cycle."""

    t_start = time.monotonic()
    timestamp = _now_iso()

    state = load_state()
    if not state.get("active", True):
        return 0

    state["status"] = "running"
    save_state(state)

    try:
        payload = generate_payload()
        synopsis = payload["synopsis"]
        next_steps = payload["next_steps"]

        _append_progress(timestamp, synopsis, next_steps)

        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        _append_observability({
            "timestamp": timestamp,
            "level": "INFO",
            "event": "update_generated",
            "summary_hash": _hash_text(synopsis),
            "execution_duration_ms": elapsed_ms,
        })

        state["last_run_iso"] = timestamp
        state["status"] = "idle"
        save_state(state)
        return 0
    except Exception as exc:  # pragma: no cover - crash logging
        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        _append_observability({
            "timestamp": timestamp,
            "level": "ERROR",
            "event": "update_failed",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "execution_duration_ms": elapsed_ms,
        })
        try:
            state["status"] = "error"
            state["last_run_iso"] = timestamp
            save_state(state)
        except Exception:
            pass
        print(f"[cerebro_tick] FATAL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
