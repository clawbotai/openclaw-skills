#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Constants
FAIL_THRESHOLD = 5
WINDOW_SECONDS = 300  # 5 minutes
COOLDOWN_SECONDS = 600  # 10 minutes

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE = SKILL_DIR.parent.parent
MEMORY_DIR = WORKSPACE / "memory"
ERROR_LOG = MEMORY_DIR / "forge-errors.json"
TICKET_LOG = MEMORY_DIR / "repair-tickets.md"


class ForgeError(Exception):
    """Raised when a forge invocation fails."""
    pass


class SkillMonitor:
    def __init__(self, workspace: Path = WORKSPACE):
        self.workspace = workspace
        self.error_log_path = ERROR_LOG
        self.ticket_log_path = TICKET_LOG

    def _load_errors(self) -> List[Dict[str, Any]]:
        if not self.error_log_path.exists():
            return []
        try:
            return json.loads(self.error_log_path.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def _save_errors(self, errors: List[Dict[str, Any]]) -> None:
        try:
            self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
            self.error_log_path.write_text(json.dumps(errors, indent=2))
        except OSError:
            pass  # simple logging should not crash the app

    def classify_error(self, error: Exception) -> str:
        msg = str(error).lower()
        transient_patterns = [
            "timeout", "rate-limit", "rate_limit", "429", "503", "502",
            "connection refused", "connection reset", "temporary",
            "resource_exhausted", "overloaded", "eagain", "server error"
        ]
        for pattern in transient_patterns:
            if pattern in msg:
                return "transient"
        return "deterministic"

    def check_circuit_breaker(self) -> Optional[str]:
        errors = self._load_errors()
        if not errors:
            return None

        now = time.time()
        # Filter for recent errors
        recent = [e for e in errors if now - e.get("timestamp", 0) < WINDOW_SECONDS]

        if len(recent) >= FAIL_THRESHOLD:
            # Check if we are in cooldown
            last_fail = max(e.get("timestamp", now) for e in recent)
            if now < (last_fail + COOLDOWN_SECONDS):
                reset_in = int((last_fail + COOLDOWN_SECONDS) - now)
                return f"Circuit breaker OPEN: {len(recent)} failures in {WINDOW_SECONDS}s. Resets in {reset_in}s."

        return None

    def create_repair_ticket(self, mode: str, args: List[str], error: Exception, priority: str = "MEDIUM") -> None:
        """Appends a structured repair ticket to memory/repair-tickets.md."""

        ticket_id = f"T-{int(time.time())}-{hashlib.md5(str(error).encode()).hexdigest()[:4]}"

        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        ticket = f"""
## Ticket {ticket_id} - Forge: {type(error).__name__}
**Status**: OPEN
**Priority**: {priority}
**Created**: {time.strftime("%Y-%m-%d %H:%M:%S")}
**Source**: Forge Skill ({mode})

### Context
- **Mode**: {mode}
- **Input**: `{args}`
- **Classification**: {self.classify_error(error)}

### Error
```text
{str(error)}
```

### Traceback
```text
{tb}
```

### Suggested Fix
- Check `SPECIFICATION.md` for requirements.
- Verify input arguments against schema.
- If deterministic, add regression test case.

---
"""
        # Append to file
        try:
            self.ticket_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ticket_log_path, "a") as f:
                f.write(ticket)
        except OSError as e:
            print(f"[Monitor] Failed to write ticket: {e}")

    def log_failure(self, mode: str, args: List[str], error: Exception, elapsed_seconds: float) -> None:
        classification = self.classify_error(error)

        # Save to JSON ledger
        errors = self._load_errors()
        entry = {
            "timestamp": time.time(),
            "mode": mode,
            "args": args,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "classification": classification,
            "elapsed_seconds": round(elapsed_seconds, 1),
        }
        errors.append(entry)
        # Prune old
        errors = errors[-50:]
        self._save_errors(errors)

        # Check circuit breaker logic for ticket generation
        circuit_msg = self.check_circuit_breaker()

        if circuit_msg:
            self.create_repair_ticket(mode, args, error, priority="CRITICAL")
        elif classification == "deterministic":
            self.create_repair_ticket(mode, args, error, priority="HIGH")

    def log_success(self, mode: str, args: List[str], elapsed_seconds: float) -> None:
        pass


# Global instance for compatibility
_monitor = SkillMonitor()


# Module-level exports for forge.py compatibility
def check_circuit_breaker() -> Optional[str]:
    return _monitor.check_circuit_breaker()


def log_failure(mode: str, args: List[str], error: Exception, elapsed_seconds: float) -> None:
    _monitor.log_failure(mode, args, error, elapsed_seconds)


def log_success(mode: str, args: List[str], elapsed_seconds: float) -> None:
    _monitor.log_success(mode, args, elapsed_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forge Skill Runtime Monitor")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("status", help="Show circuit breaker state")
    subparsers.add_parser("tickets", help="List open repair tickets")
    subparsers.add_parser("reset", help="Reset circuit breaker and clear errors")

    health_parser = subparsers.add_parser("health", help="Check skill health")
    health_parser.add_argument("skill", nargs="?", help="Specific skill name (optional)")

    args = parser.parse_args()

    if args.command == "status":
        msg = _monitor.check_circuit_breaker()
        if msg:
            print(f"Status: CLOSED (Tripped)\n{msg}")
        else:
            errors = _monitor._load_errors()
            recent = len([e for e in errors if time.time() - e.get("timestamp", 0) < WINDOW_SECONDS])
            print(f"Status: OK\nRecent errors: {recent}/{FAIL_THRESHOLD}")

    elif args.command == "tickets":
        if _monitor.ticket_log_path.exists():
            print(_monitor.ticket_log_path.read_text())
        else:
            print("No tickets found.")

    elif args.command == "reset":
        if _monitor.error_log_path.exists():
            _monitor.error_log_path.write_text("[]")
        print("Monitor reset: Error log cleared.")

    elif args.command == "health":
        # Simple health check
        msg = _monitor.check_circuit_breaker()
        status = "UNHEALTHY" if msg else "HEALTHY"
        print(f"Skill: forge\nHealth: {status}")
        if msg:
            print(msg)

    elif args.command is None:
        parser.print_help()