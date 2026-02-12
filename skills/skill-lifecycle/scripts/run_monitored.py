#!/usr/bin/env python3
"""
Monitored Skill Runner
=======================
A wrapper that routes any shell command through the SkillMonitor,
so errors are logged, classified, deduplicated, and fed into the
Evolutionary Loop's repair ticket pipeline.

Usage:
    python3 run_monitored.py <skill-name> [--timeout N] -- <command...>

Examples:
    python3 run_monitored.py email-manager -- python3 scripts/email_client.py check
    python3 run_monitored.py weather -- python3 scripts/weather.py "New York"
    python3 run_monitored.py task-planner --timeout 60 -- python3 scripts/__main__.py list

Exit codes:
    - Mirrors the wrapped command's exit code
    - 99 = usage error (bad arguments)
    - 98 = skill is quarantined (circuit breaker OPEN)

Environment:
    OPENCLAW_WORKSPACE  — workspace root (default: auto-detect from script location)
    MONITOR_VERBOSE     — set to "1" for debug output
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the scripts directory is importable
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from monitor import SkillMonitor  # noqa: E402
from schemas import MonitorConfig  # noqa: E402

VERBOSE = os.environ.get("MONITOR_VERBOSE", "") == "1"


def detect_workspace() -> Path:
    """Walk up from this script to find the workspace root."""
    # Script is at skills/skill-lifecycle/scripts/run_monitored.py
    # Workspace is 3 levels up
    candidate = SCRIPT_DIR.parent.parent.parent
    if (candidate / "AGENTS.md").exists() or (candidate / "skills").is_dir():
        return candidate
    # Fallback to env or cwd
    return Path(os.environ.get("OPENCLAW_WORKSPACE", os.getcwd()))


def parse_args(argv: list) -> tuple:
    """
    Parse: <skill-name> [--timeout N] -- <command...>
    Returns: (skill_name, timeout, command_list)
    """
    if len(argv) < 3:
        print("Usage: run_monitored.py <skill-name> [--timeout N] -- <command...>", file=sys.stderr)
        sys.exit(99)

    skill_name = argv[1]
    timeout = 300
    rest = argv[2:]

    # Parse optional flags before --
    while rest and rest[0] != "--":
        if rest[0] == "--timeout" and len(rest) > 1:
            timeout = int(rest[1])
            rest = rest[2:]
        else:
            print(f"Unknown flag: {rest[0]}", file=sys.stderr)
            sys.exit(99)

    if not rest or rest[0] != "--":
        print("Missing '--' separator before command", file=sys.stderr)
        sys.exit(99)

    command_parts = rest[1:]
    if not command_parts:
        print("No command specified after '--'", file=sys.stderr)
        sys.exit(99)

    return skill_name, timeout, command_parts


def main():
    skill_name, timeout, command_parts = parse_args(sys.argv)
    command_str = " ".join(command_parts)
    workspace = detect_workspace()

    if VERBOSE:
        print(f"[monitor] skill={skill_name} timeout={timeout}s workspace={workspace}", file=sys.stderr)
        print(f"[monitor] command: {command_str}", file=sys.stderr)

    monitor = SkillMonitor(workspace=str(workspace))

    # Check circuit breaker before running
    with monitor._lock:
        allowed, reason = monitor._check_circuit(skill_name)
    if not allowed:
        print(f"⛔ QUARANTINED: {reason}", file=sys.stderr)
        # Still output something useful
        print(json.dumps({
            "status": "quarantined",
            "skill": skill_name,
            "reason": reason,
        }))
        sys.exit(98)

    # Determine cwd: if running from a skill directory, use it
    skill_dir = workspace / "skills" / skill_name
    cwd = str(skill_dir) if skill_dir.is_dir() else str(workspace)

    # Execute through the monitor
    input_context = {"command": command_str, "cwd": cwd}

    try:
        result = subprocess.run(
            command_str,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Print stdout/stderr as the command would
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)

        if result.returncode == 0:
            # Success
            with monitor._lock:
                monitor._record_success(skill_name)
                monitor._save_ledger()
            if VERBOSE:
                print(f"[monitor] ✅ {skill_name} succeeded", file=sys.stderr)
        else:
            # Failure
            error_message = (result.stderr.strip() or result.stdout.strip() or
                             f"Exit code {result.returncode}")
            with monitor._lock:
                monitor._record_failure(
                    skill_name=skill_name,
                    error_type="SubprocessError",
                    error_message=error_message[:2000],
                    traceback_str=result.stderr[:2000] if result.stderr else "",
                    input_args=input_context,
                    exit_code=result.returncode,
                )
                monitor._save_ledger()
            if VERBOSE:
                print(f"[monitor] ❌ {skill_name} failed (exit {result.returncode})", file=sys.stderr)

        sys.exit(result.returncode)

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout}s: {command_str}"
        print(f"⏰ {error_msg}", file=sys.stderr)
        with monitor._lock:
            monitor._record_failure(
                skill_name=skill_name,
                error_type="TimeoutError",
                error_message=error_msg,
                traceback_str="",
                input_args=input_context,
                exit_code=-1,
            )
            monitor._save_ledger()
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
