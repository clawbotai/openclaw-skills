#!/usr/bin/env python3
"""
evolution_loop.py — Automatic post-work evolution pipeline.

After a WorkItem completes (or fails), this module runs the evolution chain:
1. sanity-check: OUTPUT gate on artifacts/tests/metrics
2. reflect: Encode findings into SOUL.md/TOOLS.md
3. skill-lifecycle: Monitor skill health, open repair tickets if needed

Can be triggered:
- By the orchestrator after each workflow stage
- Manually via CLI: `python3 lib/evolution_loop.py run <slug>`
- By heartbeat scanning hook events

Usage:
    from lib.evolution_loop import run_evolution, scan_pending

    # Run evolution on a specific work item
    result = run_evolution("backend-refresh-endpoint")

    # Scan for completed items that haven't been evolved yet
    pending = scan_pending()
    for slug in pending:
        run_evolution(slug)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_WORKSPACE = Path(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, str(_WORKSPACE))

from lib.shared_state import (
    WorkItem, load_item, list_items, pending_hooks,
    STATE_DIR, HOOKS_DIR, _now_iso, _append_jsonl, _read_jsonl,
)

EVOLUTION_LOG = _WORKSPACE / "state" / "evolution_log.jsonl"
EVOLUTION_STATE = _WORKSPACE / "state" / "evolution_state.json"


def _load_evolution_state() -> Dict[str, Any]:
    """Load evolution tracking state (which items have been processed)."""
    if EVOLUTION_STATE.exists():
        with open(EVOLUTION_STATE) as f:
            return json.load(f)
    return {"processed_slugs": {}, "last_scan": None}


def _save_evolution_state(state: Dict[str, Any]) -> None:
    EVOLUTION_STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(EVOLUTION_STATE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def _log_evolution(entry: Dict[str, Any]) -> None:
    EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    _append_jsonl(EVOLUTION_LOG, entry)


# ── Gate 1: Sanity Check ──

def run_sanity_check(wi: WorkItem) -> Dict[str, Any]:
    """Run OUTPUT gate on a completed/failed WorkItem.

    Returns:
        {"verdict": "pass"|"warn"|"fail", "issues": [...], "followups": [...]}
    """
    issues = []
    followups = []

    # Check: at least one artifact produced
    if not wi.artifacts:
        issues.append("No artifacts recorded — was work actually completed?")
        followups.append(f"Review {wi.slug}: no output artifacts found")

    # Check: all tests pass (if any)
    failed_tests = [t for t in wi.tests if t.get("status") not in ("pass", "skip")]
    if failed_tests:
        names = [t.get("name", "unnamed") for t in failed_tests]
        issues.append(f"{len(failed_tests)} test(s) failed: {names}")
        followups.append(f"Fix failing tests in {wi.slug}: {names}")

    # Check: coverage above threshold (if recorded)
    for m in wi.metrics:
        if m.get("name") == "test_coverage":
            val = m.get("value", 0)
            if val < 70:
                issues.append(f"Test coverage {val}% below 70% threshold")
                followups.append(f"Improve test coverage for {wi.slug} (currently {val}%)")

    # Check: if failed, ensure reason is documented
    if wi.status == "failed" and not any(
        e.get("event") == "failed" and e.get("payload", {}).get("reason")
        for e in wi.history
    ):
        issues.append("Work item failed but no failure reason recorded")

    # Determine verdict
    if not issues:
        verdict = "pass"
    elif any("failed" in i.lower() or "no artifacts" in i.lower() for i in issues):
        verdict = "fail"
    else:
        verdict = "warn"

    # Write findings/followups back to the WorkItem
    for issue in issues:
        wi.add_finding(f"[sanity-check] {issue}", author="sanity-check")
    for fu in followups:
        wi.add_followup(fu, author="sanity-check")

    return {"verdict": verdict, "issues": issues, "followups": followups}


# ── Gate 2: Reflect ──

def run_reflect(wi: WorkItem) -> Dict[str, Any]:
    """Extract learnings from a WorkItem and prepare them for encoding.

    Returns:
        {"findings_count": int, "encoded": [...], "target_files": [...]}
    """
    findings = wi.findings
    if not findings:
        return {"findings_count": 0, "encoded": [], "target_files": []}

    # Categorize findings for encoding targets
    soul_findings = []  # Behavioral learnings → SOUL.md
    tools_findings = []  # Tool/infra specifics → TOOLS.md
    skill_findings = []  # Skill-specific → skill SKILL.md

    for f in findings:
        f_lower = f.lower()
        if any(kw in f_lower for kw in ["always", "never", "pattern", "behavior", "lesson", "mistake"]):
            soul_findings.append(f)
        elif any(kw in f_lower for kw in ["config", "path", "port", "api", "key", "credential", "quirk"]):
            tools_findings.append(f)
        else:
            skill_findings.append(f)

    encoded = []
    target_files = []

    if soul_findings:
        encoded.extend(soul_findings)
        target_files.append("SOUL.md")
    if tools_findings:
        encoded.extend(tools_findings)
        target_files.append("TOOLS.md")
    if skill_findings:
        encoded.extend(skill_findings)
        skill = wi.assignee_skill
        if skill:
            target_files.append(f"skills/{skill}/SKILL.md")

    # Note: actual file writing is deferred to the agent (reflect skill).
    # We just prepare the structured input for it.
    return {
        "findings_count": len(findings),
        "encoded": encoded,
        "target_files": target_files,
        "soul": soul_findings,
        "tools": tools_findings,
        "skill": skill_findings,
    }


# ── Gate 3: Skill Lifecycle ──

def run_lifecycle_check(wi: WorkItem) -> Dict[str, Any]:
    """Check skill health based on WorkItem telemetry.

    Returns:
        {"skill": str, "health": "healthy"|"degraded"|"failing", "alerts": [...]}
    """
    skill = wi.assignee_skill or "unknown"
    alerts = []

    # Check test pass rate across all recorded tests
    total_tests = len(wi.tests)
    if total_tests > 0:
        passed = sum(1 for t in wi.tests if t.get("status") == "pass")
        pass_rate = passed / total_tests * 100
        if pass_rate < 50:
            alerts.append(f"Test pass rate critically low: {pass_rate:.0f}%")
        elif pass_rate < 80:
            alerts.append(f"Test pass rate degraded: {pass_rate:.0f}%")

    # Check for repeated failures (look at recent work items for same skill)
    try:
        recent = list_items(skill=skill)
        recent_failed = [w for w in recent if w.status == "failed"]
        if len(recent_failed) >= 3:
            alerts.append(f"Skill '{skill}' has {len(recent_failed)} failed work items — consider circuit breaker")
    except Exception:
        pass

    # Determine health
    if not alerts:
        health = "healthy"
    elif any("critically" in a.lower() or "circuit breaker" in a.lower() for a in alerts):
        health = "failing"
    else:
        health = "degraded"

    return {"skill": skill, "health": health, "alerts": alerts}


# ── Orchestrator ──

def run_evolution(slug: str, dry_run: bool = False) -> Dict[str, Any]:
    """Run the full evolution pipeline on a WorkItem.

    Args:
        slug: WorkItem slug to evolve
        dry_run: If True, don't write findings back to the WorkItem

    Returns:
        Full evolution result with sanity_check, reflect, lifecycle sections.
    """
    try:
        wi = load_item(slug)
    except FileNotFoundError:
        return {"error": f"WorkItem '{slug}' not found"}

    if wi.status not in ("done", "failed"):
        return {"error": f"WorkItem '{slug}' is {wi.status}, not done/failed — skipping evolution"}

    result = {
        "slug": slug,
        "status": wi.status,
        "timestamp": _now_iso(),
        "sanity_check": None,
        "reflect": None,
        "lifecycle": None,
    }

    # Gate 1: Sanity Check
    sc_result = run_sanity_check(wi)
    result["sanity_check"] = sc_result

    # Gate 2: Reflect (only if there are findings)
    reflect_result = run_reflect(wi)
    result["reflect"] = reflect_result

    # Gate 3: Lifecycle
    lifecycle_result = run_lifecycle_check(wi)
    result["lifecycle"] = lifecycle_result

    # Log the evolution
    _log_evolution(result)

    # Mark as processed
    state = _load_evolution_state()
    state["processed_slugs"][slug] = _now_iso()
    state["last_scan"] = _now_iso()
    _save_evolution_state(state)

    return result


def scan_pending() -> List[str]:
    """Find completed/failed WorkItems that haven't been evolved yet.

    Returns:
        List of slugs needing evolution.
    """
    state = _load_evolution_state()
    processed = set(state.get("processed_slugs", {}).keys())

    pending = []
    for wi in list_items():
        if wi.status in ("done", "failed") and wi.slug not in processed:
            pending.append(wi.slug)

    return pending


def scan_and_evolve(dry_run: bool = False) -> List[Dict[str, Any]]:
    """Scan for pending items and run evolution on all of them.

    Returns:
        List of evolution results.
    """
    results = []
    for slug in scan_pending():
        result = run_evolution(slug, dry_run=dry_run)
        results.append(result)
    return results


# ── CLI ──

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        prog="evolution-loop",
        description="Run the post-work evolution pipeline",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p = sub.add_parser("run", help="Run evolution on a specific work item")
    p.add_argument("slug")
    p.add_argument("--dry-run", action="store_true")

    # scan
    p = sub.add_parser("scan", help="Show pending items needing evolution")

    # evolve-all
    p = sub.add_parser("evolve-all", help="Scan and evolve all pending items")
    p.add_argument("--dry-run", action="store_true")

    # log
    p = sub.add_parser("log", help="Show evolution history")
    p.add_argument("--limit", type=int, default=10)

    # status
    p = sub.add_parser("status", help="Show evolution state")

    args = parser.parse_args()

    if args.command == "run":
        result = run_evolution(args.slug, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "scan":
        pending = scan_pending()
        if not pending:
            print("No pending items.")
        else:
            print(f"{len(pending)} item(s) pending evolution:")
            for slug in pending:
                print(f"  - {slug}")

    elif args.command == "evolve-all":
        results = scan_and_evolve(dry_run=args.dry_run)
        if not results:
            print("Nothing to evolve.")
        else:
            for r in results:
                verdict = r.get("sanity_check", {}).get("verdict", "?")
                health = r.get("lifecycle", {}).get("health", "?")
                findings = r.get("reflect", {}).get("findings_count", 0)
                print(f"  {r['slug']}: sanity={verdict} health={health} findings={findings}")

    elif args.command == "log":
        entries = _read_jsonl(EVOLUTION_LOG)
        for entry in entries[-args.limit:]:
            ts = entry.get("timestamp", "?")[:19]
            slug = entry.get("slug", "?")
            verdict = entry.get("sanity_check", {}).get("verdict", "?")
            print(f"  {ts}  {slug}  sanity={verdict}")

    elif args.command == "status":
        state = _load_evolution_state()
        processed = state.get("processed_slugs", {})
        print(f"Processed: {len(processed)} items")
        print(f"Last scan: {state.get('last_scan', 'never')}")
        pending = scan_pending()
        print(f"Pending: {len(pending)} items")


if __name__ == "__main__":
    main()
