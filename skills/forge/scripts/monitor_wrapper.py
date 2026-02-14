#!/usr/bin/env python3
"""
Lightweight monitor for forge skill invocations.
Logs failures, classifies errors, simple circuit breaker.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve workspace root (walk up from this script)
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent.parent  # skills/forge/scripts -> workspace
ERROR_LOG = WORKSPACE / "memory" / "forge-errors.json"

# Circuit breaker config
FAIL_THRESHOLD = 5
WINDOW_SECONDS = 300  # 5 minutes


class ForgeError(Exception):
    """Raised when a forge invocation fails."""
    pass


def _load_errors() -> List[Dict[str, Any]]:
    """Load error log from disk."""
    if not ERROR_LOG.exists():
        return []
    try:
        return json.loads(ERROR_LOG.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_errors(errors: List[Dict[str, Any]]) -> None:
    """Persist error log to disk."""
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    ERROR_LOG.write_text(json.dumps(errors, indent=2))


def classify_error(error: Exception) -> str:
    """Classify an error as transient or deterministic."""
    msg = str(error).lower()
    transient_patterns = [
        "timeout", "rate-limit", "rate_limit", "429", "503", "502",
        "connection refused", "connection reset", "temporary",
        "resource_exhausted", "overloaded",
    ]
    for pattern in transient_patterns:
        if pattern in msg:
            return "transient"
    return "deterministic"


def check_circuit_breaker() -> Optional[str]:
    """
    Check if circuit breaker is tripped.
    Returns None if OK, or a message string if tripped.
    """
    errors = _load_errors()
    now = time.time()
    recent = [e for e in errors if now - e.get("timestamp", 0) < WINDOW_SECONDS]
    if len(recent) >= FAIL_THRESHOLD:
        oldest = min(e.get("timestamp", now) for e in recent)
        reset_in = int(WINDOW_SECONDS - (now - oldest))
        return f"Circuit breaker OPEN: {len(recent)} failures in {WINDOW_SECONDS}s. Resets in {reset_in}s."
    return None


def log_failure(
    mode: str,
    args: List[str],
    error: Exception,
    elapsed_seconds: float,
) -> None:
    """Log a forge failure to the error file."""
    errors = _load_errors()
    errors.append({
        "timestamp": time.time(),
        "mode": mode,
        "args": args,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "classification": classify_error(error),
        "elapsed_seconds": round(elapsed_seconds, 1),
    })
    # Keep last 50 errors
    errors = errors[-50:]
    _save_errors(errors)


def log_success(mode: str, args: List[str], elapsed_seconds: float) -> None:
    """Optionally log success for stats. Currently a no-op to save disk."""
    pass
