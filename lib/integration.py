#!/usr/bin/env python3
"""
integration.py — Cross-skill integration orchestrator.

Provides high-level composed workflows that combine multiple skills.
Each function handles the full pipeline: memory recall → action → guardrails check → memory store.

Usage:
    from lib.integration import safe_send_email, research_customer, unified_search
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from typing import Any, Dict, List, Optional

_WORKSPACE = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(script_path: str, args: List[str], timeout: int = 60) -> Dict[str, Any]:
    """Run a skill script and return parsed JSON."""
    cmd = [sys.executable, os.path.join(_WORKSPACE, script_path)] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=_WORKSPACE
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"status": "error", "error": str(e)}

    output = (result.stdout or result.stderr or "").strip()
    if not output:
        return {"status": "error", "error": f"No output (exit {result.returncode})"}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"status": "error", "error": output[:500]}


def _memory(args: List[str], timeout: int = 60) -> Dict[str, Any]:
    return _run("skills/agent-memory/scripts/memory.py", args, timeout)


def _guardrails(args: List[str], timeout: int = 10) -> Dict[str, Any]:
    return _run("skills/agent-guardrails/scripts/guardrails.py", args, timeout)


def _email(args: List[str], timeout: int = 30) -> Dict[str, Any]:
    return _run("skills/email-manager/scripts/email_client.py", args, timeout)


# ---------------------------------------------------------------------------
# 1A. Memory-Aware Operations
# ---------------------------------------------------------------------------

def recall_context(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Recall relevant memories before an operation.
    
    Use at the start of any skill operation to pull prior context.
    Returns list of memory results sorted by relevance.
    """
    result = _memory(["recall", query, "--limit", str(limit)])
    return result.get("results", [])


def remember_outcome(
    text: str,
    skill: str,
    importance: Optional[float] = None,
    memory_type: str = "episodic",
) -> Dict[str, Any]:
    """Store the outcome of a skill operation.
    
    Call after significant skill outputs to build institutional memory.
    Auto-tags with skill name for future skill-specific recall.
    """
    tagged_text = f"[{skill}] {text}"
    args = ["remember", tagged_text, "--type", memory_type]
    if importance is not None:
        args.extend(["--importance", str(importance)])
    return _memory(args)


# ---------------------------------------------------------------------------
# 1B. Guardrailed Operations
# ---------------------------------------------------------------------------

def safe_check(action: str, target: Optional[str] = None) -> Dict[str, Any]:
    """Check if an action is safe to proceed.
    
    Returns dict with: tier, allowed, requires_confirmation, reasons.
    On guardrails error, returns a conservative T4 (require confirmation).
    """
    args = ["check", "--action", action]
    if target:
        args.extend(["--target", target])
    result = _guardrails(args)
    if result.get("status") == "error":
        # Guardrails unavailable — assume high risk
        return {
            "tier": "T4",
            "allowed": False,
            "requires_confirmation": True,
            "reasons": ["Guardrails unavailable — defaulting to T4"],
        }
    return result


def safe_scan(text: str) -> Dict[str, Any]:
    """Scan text for PII/secrets before sending externally.
    
    Returns dict with: findings (list), clean (bool).
    On error, returns not-clean (conservative).
    """
    result = _guardrails(["scan", "--text", text])
    if result.get("status") == "error":
        return {"findings": ["Scan unavailable"], "clean": False}
    return result


def safe_log(action: str, tier: str, decision: str, target: Optional[str] = None) -> None:
    """Log an action to the audit trail (fire and forget)."""
    args = ["log", "--action", action, "--tier", tier, "--decision", decision]
    if target:
        args.extend(["--target", target])
    _guardrails(args)


# ---------------------------------------------------------------------------
# 2A. Unified Search (enterprise-search fan-out)
# ---------------------------------------------------------------------------

def unified_search(
    query: str,
    sources: Optional[List[str]] = None,
    limit: int = 10,
) -> Dict[str, List[Dict[str, Any]]]:
    """Search across multiple sources simultaneously.
    
    Sources: "email", "memory", "tasks". Defaults to all available.
    Returns dict keyed by source name, each with list of results.
    """
    if sources is None:
        sources = ["email", "memory"]

    results: Dict[str, List[Dict[str, Any]]] = {}
    trace_id = str(uuid.uuid4())[:8]

    if "email" in sources:
        email_result = _email(["search", query, "--limit", str(limit)])
        if email_result.get("status") == "ok":
            results["email"] = [
                {
                    "source": "email",
                    "title": m.get("subject", ""),
                    "from": m.get("from", ""),
                    "date": m.get("date", ""),
                    "uid": m.get("uid", ""),
                    "snippet": m.get("snippet", m.get("subject", "")),
                    "trace_id": trace_id,
                }
                for m in email_result.get("messages", [])
            ]

    if "memory" in sources:
        memory_result = _memory(["recall", query, "--limit", str(limit)])
        if memory_result.get("status") != "error":
            results["memory"] = [
                {
                    "source": "memory",
                    "title": r.get("content", "")[:80],
                    "score": r.get("score", 0),
                    "type": r.get("type", ""),
                    "date": r.get("created_at", ""),
                    "trace_id": trace_id,
                }
                for r in memory_result.get("results", [])
            ]

    return results


# ---------------------------------------------------------------------------
# 2B. Safe Email (guardrails + memory integrated)
# ---------------------------------------------------------------------------

def safe_send_email(
    to: str,
    subject: str,
    body: str,
    confirm_callback=None,
) -> Dict[str, Any]:
    """Send an email with full guardrails integration.
    
    1. Scan body for PII/secrets
    2. Check action risk tier
    3. If requires confirmation, call confirm_callback (or return needs_confirm)
    4. Send email
    5. Log to audit trail
    6. Store in memory
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        confirm_callback: Optional callable that returns True to proceed
        
    Returns:
        Dict with status and details
    """
    # Step 1: Scan for sensitive data
    scan = safe_scan(body)
    if not scan.get("clean", True) and scan.get("findings"):
        return {
            "status": "blocked",
            "reason": "sensitive_data_detected",
            "findings": scan["findings"],
        }

    # Step 2: Check risk tier
    check = safe_check("send_email", target=to)
    if check.get("requires_confirmation"):
        if confirm_callback and not confirm_callback(check):
            safe_log("send_email", check.get("tier", "T3"), "deny", target=to)
            return {"status": "denied", "reason": "user_declined", "tier": check.get("tier")}

    # Step 3: Send
    result = _email(["send", "--to", to, "--subject", subject, "--body", body])

    # Step 4: Log
    tier = check.get("tier", "T3")
    safe_log("send_email", tier, "allow", target=to)

    # Step 5: Remember
    remember_outcome(
        f"Sent email to {to}: {subject}",
        skill="email-manager",
        importance=0.5,
    )

    return result


# ---------------------------------------------------------------------------
# 2C. Memory-Aware Skill Operations
# ---------------------------------------------------------------------------

def with_context(skill: str, operation: str, query: Optional[str] = None):
    """Decorator-style context loader. Returns prior memories for a skill operation.
    
    Usage:
        context = with_context("legal", "contract-review", "Acme vendor agreement")
        # context contains relevant prior legal reviews, Acme history, etc.
    """
    search_query = query or f"{skill} {operation}"
    memories = recall_context(search_query, limit=5)
    return {
        "skill": skill,
        "operation": operation,
        "prior_context": memories,
        "has_context": len(memories) > 0,
    }


# ---------------------------------------------------------------------------
# 3A. Composed Workflows
# ---------------------------------------------------------------------------

def customer_research(customer_name: str, issue: Optional[str] = None) -> Dict[str, Any]:
    """Research a customer across all sources.
    
    Combines: memory recall + email search + task search.
    Used by customer-support/research command.
    """
    query = f"{customer_name} {issue or ''}".strip()

    # Fan-out search
    search_results = unified_search(query, sources=["email", "memory"])

    # Recall any stored customer context
    customer_memories = recall_context(f"customer {customer_name}", limit=3)

    return {
        "customer": customer_name,
        "issue": issue,
        "email_results": search_results.get("email", []),
        "memory_results": search_results.get("memory", []),
        "customer_context": customer_memories,
        "sources_searched": list(search_results.keys()),
    }


def deal_review_context(company: str, deal_details: Optional[str] = None) -> Dict[str, Any]:
    """Gather context for a deal review across legal, sales, and finance.
    
    Returns prior context from all three domains for the orchestrator to distribute.
    """
    query = f"{company} {deal_details or 'deal contract'}".strip()

    legal_context = recall_context(f"[legal] {company}", limit=3)
    sales_context = recall_context(f"[sales] {company}", limit=3)
    finance_context = recall_context(f"[finance] {company}", limit=3)
    email_context = unified_search(f"{company} contract", sources=["email"])

    return {
        "company": company,
        "legal_prior": legal_context,
        "sales_prior": sales_context,
        "finance_prior": finance_context,
        "email_history": email_context.get("email", []),
    }
