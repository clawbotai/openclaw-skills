#!/usr/bin/env python3
"""
guardrails_client.py — Thin subprocess wrapper for agent-guardrails.

Provides a simple Python API for any skill to check action risk tiers,
scan for sensitive data, and log decisions to the audit trail.

Usage:
    from lib.guardrails_client import check_action, scan_text

    result = check_action("send_email", target="ceo@company.com")
    if result["requires_confirmation"]:
        print(f"Action is {result['tier_label']} risk: {result['reasons']}")

    scan = scan_text("My SSN is 123-45-6789")
    if scan["findings"]:
        print(f"Sensitive data detected: {scan['findings']}")
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

_WORKSPACE = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
_GUARDRAILS_SCRIPT = os.path.join(
    _WORKSPACE, "skills", "agent-guardrails", "scripts", "guardrails.py"
)


def _run_guardrails_cmd(args: List[str], timeout: int = 10) -> Dict[str, Any]:
    """Execute a guardrails.py subcommand and return parsed JSON.

    Args:
        args: Arguments to pass to guardrails.py.
        timeout: Max seconds to wait.

    Returns:
        Parsed JSON dict from stdout.

    Raises:
        RuntimeError: If the command fails or returns invalid JSON.
    """
    cmd = [sys.executable, _GUARDRAILS_SCRIPT] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_WORKSPACE,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"guardrails.py timed out after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError(f"guardrails.py not found at {_GUARDRAILS_SCRIPT}")

    output = result.stdout.strip()
    if not output:
        output = result.stderr.strip()

    if not output:
        raise RuntimeError(
            f"guardrails.py returned no output (exit {result.returncode})"
        )

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError(f"guardrails.py returned invalid JSON: {output[:200]}")


def check_action(
    action: str,
    target: Optional[str] = None,
    context: Optional[str] = None,
    session: Optional[str] = None,
) -> Dict[str, Any]:
    """Classify an action's risk tier (T1-T4).

    Args:
        action: Action type (e.g. "send_email", "deploy_site", "delete_file").
        target: Target of the action (recipient, path, URL, etc.).
        context: Additional context about the action.
        session: Session identifier for audit trail.

    Returns:
        Dict with: tier (T1-T4), tier_label, allowed, requires_confirmation, reasons.
    """
    args = ["check", "--action", action]
    if target:
        args.extend(["--target", target])
    if context:
        args.extend(["--context", context])
    if session:
        args.extend(["--session", session])
    return _run_guardrails_cmd(args)


def scan_text(text: str) -> Dict[str, Any]:
    """Scan text for sensitive data patterns (SSN, credit cards, API keys, etc.).

    Args:
        text: The text to scan.

    Returns:
        Dict with: findings (list of detected patterns), clean (bool).
    """
    return _run_guardrails_cmd(["scan", text])


def log_action(
    action: str,
    tier: str,
    decision: str,
    target: Optional[str] = None,
    context: Optional[str] = None,
    session: Optional[str] = None,
) -> Dict[str, Any]:
    """Record an action decision to the audit trail.

    Args:
        action: Action type.
        tier: Risk tier (T1-T4).
        decision: "allow", "deny", or "escalate".
        target: Action target.
        context: Additional context.
        session: Session identifier.

    Returns:
        Dict with status confirmation.
    """
    args = ["log", "--action", action, "--tier", tier, "--decision", decision]
    if target:
        args.extend(["--target", target])
    if context:
        args.extend(["--context", context])
    if session:
        args.extend(["--session", session])
    return _run_guardrails_cmd(args)


def is_safe(action: str, target: Optional[str] = None) -> bool:
    """Quick check: is this action safe to proceed without confirmation?

    Args:
        action: Action type.
        target: Optional target.

    Returns:
        True if action is T1/T2 and doesn't require confirmation.
    """
    try:
        result = check_action(action, target=target)
        return result.get("allowed", False) and not result.get("requires_confirmation", True)
    except RuntimeError:
        # If guardrails is unavailable, err on the side of caution
        return False
