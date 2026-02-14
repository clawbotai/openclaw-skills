"""Audit logger — records every state transition and action to JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class AuditLog:
    """Accumulates structured audit events and writes them to a JSON file."""

    def __init__(self) -> None:
        self._start_time: str = datetime.now(timezone.utc).isoformat()
        self._events: list[dict[str, object]] = []

    def _stamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_state_transition(self, from_state: str, to_state: str) -> None:
        """Record an FSM state transition."""
        self._events.append({
            "type": "state_transition",
            "from": from_state,
            "to": to_state,
            "timestamp": self._stamp(),
        })

    def record_snapshot(self, snapshot_id: str) -> None:
        """Record snapshot creation."""
        self._events.append({
            "type": "snapshot_created",
            "snapshot_id": snapshot_id,
            "timestamp": self._stamp(),
        })

    def record_dms_armed(self, pid: int, timeout: int) -> None:
        """Record Dead Man's Switch arming."""
        self._events.append({
            "type": "dms_armed",
            "pid": pid,
            "timeout_seconds": timeout,
            "timestamp": self._stamp(),
        })

    def record_disabled_daemons(self, actions: list[dict[str, str]]) -> None:
        """Record the list of daemons that were disabled."""
        self._events.append({
            "type": "daemons_disabled",
            "count": len(actions),
            "actions": actions,
            "timestamp": self._stamp(),
        })

    def record_payload_launch(self, pid: int, binary: str) -> None:
        """Record workload launch."""
        self._events.append({
            "type": "payload_launched",
            "pid": pid,
            "binary": binary,
            "timestamp": self._stamp(),
        })

    def record_failure(self, error_type: str, message: str, context: Optional[dict[str, object]] = None, traceback: Optional[str] = None) -> None:
        """Record a failure event (transient or deterministic)."""
        self._events.append({
            "type": "failure",
            "error_type": error_type,
            "message": message,
            "context": context or {},
            "traceback": traceback,
            "timestamp": self._stamp(),
        })

    def finalize(self, final_state: str) -> str:
        """Write the audit log to disk and return the file path."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"ban_audit_{ts}.json"
        record = {
            "ban_version": "1.0.0",
            "started": self._start_time,
            "finalized": self._stamp(),
            "final_state": final_state,
            "events": self._events,
        }
        path = Path(filename)
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return str(path.resolve())
