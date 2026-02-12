#!/usr/bin/env python3
"""
agent-guardrails / guardrails.py
=================================
Advisory safety layer for autonomous AI agents.

Implements the "Check → Scan → Act" loop:
  1. check  — Classify an action into a risk tier (T1–T4)
  2. scan   — Detect sensitive data patterns in text
  3. audit  — Review the action audit trail
  4. log    — Record an action decision
  5. stats  — Guardrails health report

All actions are classified against a policy file (policies.json) and
logged to an SQLite audit trail.  This is an ADVISORY system — the
agent voluntarily consults it before acting.  It is not a technical
sandbox or middleware intercept.

Architecture influenced by:
  - "Policy as Prompt" (arxiv 2509.23994): least-privilege runtime classifiers
  - OWASP Top 10 for LLM Apps: prompt injection, insecure output handling
  - EU AI Act conformity: tiered risk classification with audit trail
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SKILL_DIR = Path(__file__).resolve().parent.parent  # .../skills/agent-guardrails
_DEFAULT_POLICY = _SKILL_DIR / "policies.json"
_WORKSPACE = _SKILL_DIR.parent.parent  # .../skills/../ = workspace root

_DEFAULT_DB_DIR = os.environ.get(
    "GUARDRAILS_DB_DIR",
    str(_WORKSPACE / "memory"),
)
_DEFAULT_DB_PATH = os.path.join(_DEFAULT_DB_DIR, "guardrails_audit.db")

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          TEXT PRIMARY KEY,
    timestamp   REAL NOT NULL,
    action      TEXT NOT NULL,
    target      TEXT,
    tier        TEXT NOT NULL,
    decision    TEXT NOT NULL CHECK (decision IN ('APPROVED','DENIED','PENDING','AUTO')),
    reason      TEXT,
    session     TEXT DEFAULT 'main',
    scan_result TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action    ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_tier      ON audit_log(tier);

CREATE TABLE IF NOT EXISTS approval_cache (
    action_target_hash TEXT PRIMARY KEY,
    approved_at        REAL NOT NULL,
    tier               TEXT NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open the audit SQLite database with WAL mode.

    Args:
        db_path: Override path.  Defaults to memory/guardrails_audit.db.

    Returns:
        sqlite3.Connection with row_factory = sqlite3.Row.
    """
    path = db_path or _DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


def _new_id() -> str:
    """Generate a short unique ID for audit log entries."""
    import uuid
    return str(uuid.uuid4())[:12]


# ---------------------------------------------------------------------------
# Policy loader
# ---------------------------------------------------------------------------

_DEFAULT_POLICY_FALLBACK = {
    "tiers": {
        "T1": {"label": "Safe"},
        "T2": {"label": "Low"},
        "T3": {"label": "Medium", "rate_limit_per_minute": 5},
        "T4": {"label": "High", "rate_limit_per_hour": 3, "requires_confirmation": True},
    },
    "rules": [],
    "sensitive_paths": [".env", ".ssh", "/etc/", ".pem", ".key"],
    "sensitive_patterns": {},
    "prompt_injection_patterns": [],
    "defaults": {
        "unknown_action": "T3",
        "session_cache_seconds": 300,
    },
}


def _load_policy(policy_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the policy file, falling back to safe defaults if missing.

    Args:
        policy_path: Path to policies.json.

    Returns:
        Parsed policy dict.
    """
    path = policy_path or str(_DEFAULT_POLICY)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            _warn(f"Failed to load {path}: {exc}. Using default policy.")
    else:
        _warn(f"Policy file not found: {path}. Using default fallback (everything = T3).")
    return _DEFAULT_POLICY_FALLBACK


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _json_out(data: Any) -> None:
    """Print structured JSON to stdout."""
    print(json.dumps(data, indent=2, default=str))


def _error_out(message: str, code: str = "ERROR") -> None:
    """Print a JSON error to stderr and exit 1."""
    print(json.dumps({"status": "error", "code": code, "message": message}),
          file=sys.stderr)
    sys.exit(1)


def _warn(message: str) -> None:
    """Print a warning to stderr (non-fatal)."""
    print(json.dumps({"warning": message}), file=sys.stderr)


# ---------------------------------------------------------------------------
# CHECK — classify an action
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> None:
    """Classify an action into a risk tier and check rate limits.

    Classification pipeline:
      1. Match action against policy rules → base tier
      2. Evaluate conditions (sensitive paths, sudo, etc.) → may promote tier
      3. Check quiet hours → may promote by 1 tier
      4. Check session approval cache → may downgrade T3 to auto-approve
      5. Check rate limits → may deny

    Args:
        args: Parsed CLI args with .action, .target, .context, .session, .db, .policy.
    """
    policy = _load_policy(args.policy)
    action = args.action
    target = getattr(args, "target", "") or ""
    context = getattr(args, "context", "") or ""
    session = getattr(args, "session", "main") or "main"

    # Step 1: Find matching rule
    base_tier = policy.get("defaults", {}).get("unknown_action", "T3")
    matched_rule = None  # type: Optional[Dict]
    for rule in policy.get("rules", []):
        if rule["action"] == action:
            base_tier = rule["tier"]
            matched_rule = rule
            break

    tier = base_tier
    reasons = []  # type: List[str]

    # Step 2: Evaluate conditions
    if matched_rule and "conditions" in matched_rule:
        conditions = matched_rule["conditions"]

        # Sensitive path check
        if "sensitive_path" in conditions:
            sensitive_paths = policy.get("sensitive_paths", [])
            if _matches_sensitive_path(target, sensitive_paths):
                promoted = conditions["sensitive_path"]
                if _tier_rank(promoted) > _tier_rank(tier):
                    reasons.append(f"Target matches sensitive path → promoted to {promoted}")
                    tier = promoted

        # Outside workspace check
        if "outside_workspace" in conditions:
            if target and not _is_within_workspace(target):
                promoted = conditions["outside_workspace"]
                if _tier_rank(promoted) > _tier_rank(tier):
                    reasons.append(f"Target outside workspace → promoted to {promoted}")
                    tier = promoted

        # Sudo check
        if "contains_sudo" in conditions:
            full_text = f"{target} {context}".lower()
            if "sudo " in full_text:
                promoted = conditions["contains_sudo"]
                if _tier_rank(promoted) > _tier_rank(tier):
                    reasons.append(f"Contains sudo → promoted to {promoted}")
                    tier = promoted

        # rm -rf check
        if "contains_rm_rf" in conditions:
            full_text = f"{target} {context}".lower()
            if re.search(r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b", full_text):
                promoted = conditions["contains_rm_rf"]
                if _tier_rank(promoted) > _tier_rank(tier):
                    reasons.append(f"Contains rm -rf → promoted to {promoted}")
                    tier = promoted

        # Unknown recipient check
        if "to_unknown" in conditions or "new_recipient" in conditions:
            known = policy.get("known_contacts", [])
            cond_key = "to_unknown" if "to_unknown" in conditions else "new_recipient"
            if target and target not in known:
                promoted = conditions[cond_key]
                if _tier_rank(promoted) > _tier_rank(tier):
                    reasons.append(f"Unknown recipient '{target}' → promoted to {promoted}")
                    tier = promoted

    # Step 3: Quiet hours promotion
    if policy.get("defaults", {}).get("quiet_hours", {}).get("promote_tier"):
        if _is_quiet_hours(policy["defaults"]["quiet_hours"]):
            new_tier = _promote_tier(tier)
            if new_tier != tier:
                reasons.append(f"Quiet hours active → promoted {tier} to {new_tier}")
                tier = new_tier

    # Step 4: Check session approval cache (T3 downgrade)
    conn = _get_db(args.db)
    try:
        requires_confirmation = False
        tier_config = policy.get("tiers", {}).get(tier, {})

        if tier_config.get("requires_confirmation", False):
            requires_confirmation = True

        # Session cache: if same action+target was approved recently, auto-approve
        if tier == "T3" and not requires_confirmation:
            cache_ttl = policy.get("defaults", {}).get("session_cache_seconds", 300)
            if _check_approval_cache(conn, action, target, cache_ttl):
                reasons.append(f"Same action+target approved within {cache_ttl}s → auto-approve")
                requires_confirmation = False

        # Step 5: Rate limit check
        allowed = True
        rate_limit_msg = None  # type: Optional[str]

        if "rate_limit_per_minute" in tier_config:
            limit = tier_config["rate_limit_per_minute"]
            count = _count_recent_actions(conn, tier, window_seconds=60)
            if count >= limit:
                allowed = False
                rate_limit_msg = f"Rate limit exceeded: {count}/{limit} {tier} actions in last minute"
                reasons.append(rate_limit_msg)

        if "rate_limit_per_hour" in tier_config:
            limit = tier_config["rate_limit_per_hour"]
            count = _count_recent_actions(conn, tier, window_seconds=3600)
            if count >= limit:
                allowed = False
                rate_limit_msg = f"Rate limit exceeded: {count}/{limit} {tier} actions in last hour"
                reasons.append(rate_limit_msg)

        if not reasons:
            reasons.append(f"Matched rule: {action} → {tier}")

        _json_out({
            "status": "ok",
            "action": action,
            "target": target,
            "tier": tier,
            "tier_label": tier_config.get("label", tier),
            "allowed": allowed,
            "requires_confirmation": requires_confirmation,
            "reasons": reasons,
        })
    finally:
        conn.close()


def _tier_rank(tier: str) -> int:
    """Convert tier string to numeric rank for comparison."""
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(tier, 3)


def _promote_tier(tier: str) -> str:
    """Promote a tier by one level (T1→T2, T2→T3, T3→T4, T4→T4)."""
    mapping = {"T1": "T2", "T2": "T3", "T3": "T4", "T4": "T4"}
    return mapping.get(tier, tier)


def _matches_sensitive_path(target: str, sensitive_paths: List[str]) -> bool:
    """Check if a target path matches any sensitive path pattern."""
    if not target:
        return False
    target_lower = target.lower()
    for pattern in sensitive_paths:
        if pattern.lower() in target_lower:
            return True
    return False


def _is_within_workspace(target: str) -> bool:
    """Check if a target path is within the workspace directory."""
    try:
        target_real = os.path.realpath(os.path.expanduser(target))
        workspace_real = os.path.realpath(str(_WORKSPACE))
        return target_real.startswith(workspace_real)
    except (OSError, ValueError):
        return False


def _is_quiet_hours(config: Dict) -> bool:
    """Check if the current time falls within quiet hours."""
    try:
        now = datetime.now()
        start_h, start_m = map(int, config.get("start", "23:00").split(":"))
        end_h, end_m = map(int, config.get("end", "08:00").split(":"))

        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        now_minutes = now.hour * 60 + now.minute

        if start_minutes > end_minutes:  # crosses midnight
            return now_minutes >= start_minutes or now_minutes < end_minutes
        else:
            return start_minutes <= now_minutes < end_minutes
    except (ValueError, AttributeError):
        return False


def _check_approval_cache(
    conn: sqlite3.Connection,
    action: str,
    target: str,
    ttl_seconds: int,
) -> bool:
    """Check if this action+target was recently approved (session cache).

    Prevents user fatigue by auto-approving repeated safe operations
    (e.g., multiple git pushes in a row).
    """
    key = hashlib.sha256(f"{action}:{target}".encode()).hexdigest()[:16]
    cutoff = time.time() - ttl_seconds
    row = conn.execute(
        "SELECT approved_at FROM approval_cache WHERE action_target_hash = ? AND approved_at > ?",
        (key, cutoff),
    ).fetchone()
    return row is not None


def _update_approval_cache(
    conn: sqlite3.Connection,
    action: str,
    target: str,
    tier: str,
) -> None:
    """Record an approval in the session cache."""
    key = hashlib.sha256(f"{action}:{target}".encode()).hexdigest()[:16]
    conn.execute(
        """INSERT OR REPLACE INTO approval_cache (action_target_hash, approved_at, tier)
           VALUES (?, ?, ?)""",
        (key, time.time(), tier),
    )
    conn.commit()


def _count_recent_actions(
    conn: sqlite3.Connection,
    tier: str,
    window_seconds: int,
) -> int:
    """Count approved actions of a given tier within a time window."""
    cutoff = time.time() - window_seconds
    row = conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE tier = ? AND decision = 'APPROVED' AND timestamp > ?",
        (tier, cutoff),
    ).fetchone()
    return row[0] if row else 0


# ---------------------------------------------------------------------------
# SCAN — detect sensitive data
# ---------------------------------------------------------------------------

def cmd_scan(args: argparse.Namespace) -> None:
    """Scan text for sensitive data patterns (API keys, PII, credentials).

    Also checks for prompt injection patterns.

    Args:
        args: Parsed CLI args with .text (str) or .file (str).
    """
    policy = _load_policy(args.policy)

    # Get text from arg or file
    text = getattr(args, "text", None)
    if not text:
        filepath = getattr(args, "file", None)
        if filepath and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        else:
            _error_out("Provide --text or --file to scan.", "NO_INPUT")

    findings = []  # type: List[Dict[str, str]]
    injection_detected = False

    # Sensitive data patterns
    for name, pattern in policy.get("sensitive_patterns", {}).items():
        try:
            matches = re.findall(pattern, text)
            if matches:
                # Redact the actual values for safety
                findings.append({
                    "type": name,
                    "count": len(matches),
                    "sample": _redact(matches[0]),
                })
        except re.error:
            continue

    # Prompt injection patterns
    for pattern in policy.get("prompt_injection_patterns", []):
        try:
            if re.search(pattern, text, re.IGNORECASE):
                injection_detected = True
                findings.append({
                    "type": "prompt_injection",
                    "count": 1,
                    "pattern": pattern,
                })
        except re.error:
            continue

    safe = len(findings) == 0

    _json_out({
        "status": "ok",
        "safe": safe,
        "injection_detected": injection_detected,
        "findings": findings,
        "scanned_length": len(text),
    })


def _redact(value: str, show: int = 4) -> str:
    """Redact a sensitive value, showing only the first few characters."""
    if len(value) <= show + 4:
        return "****"
    return value[:show] + "****" + value[-2:]


# ---------------------------------------------------------------------------
# LOG — record an action decision
# ---------------------------------------------------------------------------

def cmd_log(args: argparse.Namespace) -> None:
    """Record an action decision in the audit trail.

    Args:
        args: Parsed CLI args with .action, .tier, .decision, .target,
              .reason, .session, .scan_result.
    """
    conn = _get_db(args.db)
    try:
        entry_id = _new_id()
        now = time.time()

        conn.execute(
            """INSERT INTO audit_log
               (id, timestamp, action, target, tier, decision, reason, session, scan_result)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_id,
                now,
                args.action,
                getattr(args, "target", None),
                args.tier,
                args.decision.upper(),
                getattr(args, "reason", None),
                getattr(args, "session", "main") or "main",
                getattr(args, "scan_result", None),
            ),
        )

        # Update approval cache if approved
        if args.decision.upper() == "APPROVED":
            _update_approval_cache(
                conn, args.action,
                getattr(args, "target", "") or "",
                args.tier,
            )

        conn.commit()
        _json_out({
            "status": "logged",
            "id": entry_id,
            "action": args.action,
            "tier": args.tier,
            "decision": args.decision.upper(),
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AUDIT — review the trail
# ---------------------------------------------------------------------------

def cmd_audit(args: argparse.Namespace) -> None:
    """Fetch recent audit log entries.

    Args:
        args: Parsed CLI args with .limit, .tier, .since, .action.
    """
    conn = _get_db(args.db)
    try:
        conditions = []  # type: List[str]
        params = []  # type: List[Any]

        tier_filter = getattr(args, "tier", None)
        if tier_filter:
            conditions.append("tier = ?")
            params.append(tier_filter)

        action_filter = getattr(args, "action_filter", None)
        if action_filter:
            conditions.append("action = ?")
            params.append(action_filter)

        since = getattr(args, "since", None)
        if since:
            try:
                dt = datetime.fromisoformat(since)
                conditions.append("timestamp >= ?")
                params.append(dt.timestamp())
            except ValueError:
                _error_out(f"Invalid date: {since}", "BAD_DATE")

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        limit = getattr(args, "limit", 20) or 20
        params.append(limit)

        rows = conn.execute(
            f"""SELECT id, timestamp, action, target, tier, decision, reason, session
                FROM audit_log {where}
                ORDER BY timestamp DESC
                LIMIT ?""",
            params,
        ).fetchall()

        entries = []
        for row in rows:
            entry = dict(row)
            entry["time_iso"] = datetime.fromtimestamp(
                entry["timestamp"], tz=timezone.utc
            ).isoformat()
            entries.append(entry)

        _json_out({
            "status": "ok",
            "count": len(entries),
            "entries": entries,
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# STATS — guardrails health report
# ---------------------------------------------------------------------------

def cmd_stats(args: argparse.Namespace) -> None:
    """Guardrails system health report: action counts, rate limits, alerts."""
    conn = _get_db(args.db)
    policy = _load_policy(args.policy)
    now = time.time()

    try:
        total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        # Counts by tier
        tier_counts = {}
        for tier in ("T1", "T2", "T3", "T4"):
            tier_counts[tier] = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE tier = ?", (tier,)
            ).fetchone()[0]

        # Counts by decision
        decision_counts = {}
        for dec in ("APPROVED", "DENIED", "PENDING", "AUTO"):
            decision_counts[dec] = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE decision = ?", (dec,)
            ).fetchone()[0]

        # Current rate usage
        t3_minute = _count_recent_actions(conn, "T3", 60)
        t4_hour = _count_recent_actions(conn, "T4", 3600)
        t3_limit = policy.get("tiers", {}).get("T3", {}).get("rate_limit_per_minute", 5)
        t4_limit = policy.get("tiers", {}).get("T4", {}).get("rate_limit_per_hour", 3)

        # Recent denials
        denials = conn.execute(
            """SELECT action, target, reason, timestamp FROM audit_log
               WHERE decision = 'DENIED' ORDER BY timestamp DESC LIMIT 5"""
        ).fetchall()

        # DB size
        db_path = args.db or _DEFAULT_DB_PATH
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        _json_out({
            "status": "ok",
            "total_logged": total,
            "by_tier": tier_counts,
            "by_decision": decision_counts,
            "rate_limits": {
                "T3": f"{t3_minute}/{t3_limit} per minute",
                "T4": f"{t4_hour}/{t4_limit} per hour",
            },
            "recent_denials": [dict(d) for d in denials],
            "db_size_bytes": db_size,
            "policy_path": str(_DEFAULT_POLICY),
            "policy_loaded": os.path.exists(str(_DEFAULT_POLICY)),
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI for guardrails commands."""
    parser = argparse.ArgumentParser(
        prog="guardrails.py",
        description="Advisory safety layer for OpenClaw autonomous agents.",
    )
    parser.add_argument("--db", default=None, help="Override audit DB path")
    parser.add_argument("--policy", default=None, help="Override policies.json path")

    subs = parser.add_subparsers(dest="command", required=True)

    # check
    p_check = subs.add_parser("check", help="Classify an action's risk tier")
    p_check.add_argument("--action", required=True, help="Action type (e.g., send_email)")
    p_check.add_argument("--target", default="", help="Target (path, recipient, etc.)")
    p_check.add_argument("--context", default="", help="Additional context")
    p_check.add_argument("--session", default="main", help="Session identifier")

    # scan
    p_scan = subs.add_parser("scan", help="Scan text for sensitive data")
    p_scan.add_argument("--text", default=None, help="Text to scan")
    p_scan.add_argument("--file", default=None, help="File to scan")

    # log
    p_log = subs.add_parser("log", help="Record an action decision")
    p_log.add_argument("--action", required=True, help="Action type")
    p_log.add_argument("--tier", required=True, choices=["T1", "T2", "T3", "T4"])
    p_log.add_argument("--decision", required=True,
                       choices=["APPROVED", "DENIED", "PENDING", "AUTO"])
    p_log.add_argument("--target", default=None)
    p_log.add_argument("--reason", default=None)
    p_log.add_argument("--session", default="main")
    p_log.add_argument("--scan-result", default=None)

    # audit
    p_audit = subs.add_parser("audit", help="Review audit trail")
    p_audit.add_argument("--limit", type=int, default=20)
    p_audit.add_argument("--tier", default=None, choices=["T1", "T2", "T3", "T4"])
    p_audit.add_argument("--action-filter", default=None, help="Filter by action type")
    p_audit.add_argument("--since", default=None, help="ISO date cutoff")

    # stats
    subs.add_parser("stats", help="Guardrails health report")

    return parser


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_DISPATCH = {
    "check": cmd_check,
    "scan": cmd_scan,
    "log": cmd_log,
    "audit": cmd_audit,
    "stats": cmd_stats,
}

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handler = _DISPATCH.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)
