#!/usr/bin/env python3
"""
agent-orchestration / orchestrator.py
======================================
Stateless workflow lifecycle manager for multi-agent orchestration.

Tracks active workflows in a local JSON ledger (memory/workflows.json).
The parent agent (orchestrator) uses this to:
  1. Create a plan — register subtasks with IDs
  2. Update tasks — mark in_progress / completed / failed
  3. Check status — see overall progress
  4. Aggregate results — combine completed outputs into final deliverable

Design principles (arXiv 2510.25445, LangGraph, CrewAI):
  - Stateless: all state lives in the JSON ledger, not in memory
  - Recoverable: if the session resets, the agent can resume from the ledger
  - Pattern-aware: workflows are tagged with their orchestration pattern
  - Failure-tolerant: failed subtasks don't block the whole workflow

CLI:
    python3 orchestrator.py create --type fan_out --subtasks '[...]'
    python3 orchestrator.py update --id <wf_id> --task-id <t_id> --status completed --result "..."
    python3 orchestrator.py status --id <wf_id>
    python3 orchestrator.py aggregate --id <wf_id>
    python3 orchestrator.py list [--active]
    python3 orchestrator.py cleanup [--days 7]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SKILL_DIR = Path(__file__).resolve().parent.parent
_WORKSPACE = _SKILL_DIR.parent.parent  # skills/../ = workspace root
_LEDGER_DIR = os.environ.get(
    "ORCHESTRATION_DIR",
    str(_WORKSPACE / "memory"),
)
_LEDGER_PATH = os.path.join(_LEDGER_DIR, "workflows.json")

# ---------------------------------------------------------------------------
# Workflow statuses
# ---------------------------------------------------------------------------

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

WORKFLOW_ACTIVE_STATES = {STATUS_PENDING, STATUS_IN_PROGRESS}
TASK_TERMINAL_STATES = {STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED}

# ---------------------------------------------------------------------------
# Ledger I/O
# ---------------------------------------------------------------------------


class WorkflowManager:
    """Manages workflow state via a local JSON ledger.

    All methods are stateless — they read the ledger, modify it, and
    write it back.  Thread safety is NOT guaranteed (single-agent usage).

    The ledger structure:
    ```json
    {
      "workflows": {
        "<workflow_id>": {
          "id": "...",
          "type": "fan_out|pipeline|supervisor|expert_panel|map_reduce",
          "status": "pending|in_progress|completed|failed",
          "created_at": 1234567890.0,
          "updated_at": 1234567890.0,
          "subtasks": [
            {
              "id": "task_1",
              "label": "Review auth module",
              "status": "pending|in_progress|completed|failed",
              "session_key": null,
              "result": null,
              "started_at": null,
              "completed_at": null,
              "retries": 0
            }
          ],
          "metadata": {}
        }
      }
    }
    ```
    """

    def __init__(self, ledger_path: Optional[str] = None):
        """Initialize the WorkflowManager.

        Args:
            ledger_path: Override for the ledger file path.
        """
        self._path = ledger_path or _LEDGER_PATH

    def _read(self) -> Dict[str, Any]:
        """Read the ledger from disk.

        Returns:
            Parsed ledger dict.  Returns empty structure if file
            doesn't exist or is corrupt.
        """
        if not os.path.exists(self._path):
            return {"workflows": {}}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "workflows" not in data:
                    data["workflows"] = {}
                return data
        except (json.JSONDecodeError, OSError):
            return {"workflows": {}}

    def _write(self, data: Dict[str, Any]) -> None:
        """Write the ledger to disk.

        Creates parent directories if needed.

        Args:
            data: The full ledger dict to write.
        """
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except OSError as exc:
            _error_out(f"Failed to write ledger: {exc}", "IO_ERROR")

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def create_plan(
        self,
        workflow_type: str,
        subtasks: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new workflow and register its subtasks.

        Args:
            workflow_type: Orchestration pattern name
                (fan_out, pipeline, supervisor, expert_panel, map_reduce).
            subtasks: List of dicts with at least "id" and "label" keys.
                Optional: "session_key" if already spawned.
            metadata: Arbitrary metadata to attach to the workflow
                (e.g., user request, model preferences).

        Returns:
            The generated workflow ID.
        """
        now = time.time()
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"

        tasks = []  # type: List[Dict[str, Any]]
        for i, st in enumerate(subtasks):
            task_id = st.get("id", f"task_{i + 1}")
            tasks.append({
                "id": task_id,
                "label": st.get("label", f"Subtask {i + 1}"),
                "status": STATUS_PENDING,
                "session_key": st.get("session_key"),
                "result": None,
                "started_at": None,
                "completed_at": None,
                "retries": 0,
            })

        workflow = {
            "id": workflow_id,
            "type": workflow_type,
            "status": STATUS_PENDING,
            "created_at": now,
            "updated_at": now,
            "subtasks": tasks,
            "metadata": metadata or {},
        }

        data = self._read()
        data["workflows"][workflow_id] = workflow
        self._write(data)
        return workflow_id

    def update_task(
        self,
        workflow_id: str,
        task_id: str,
        status: str,
        result: Optional[str] = None,
        session_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update the status of a subtask within a workflow.

        Also updates the parent workflow status:
          - If any task is in_progress → workflow is in_progress
          - If all tasks are terminal → workflow is completed (or failed
            if ALL failed)

        Args:
            workflow_id: The workflow to update.
            task_id: The subtask to update.
            status: New status (pending, in_progress, completed, failed, cancelled).
            result: Result text (for completed tasks).
            session_key: Session key of the sub-agent (for tracking).

        Returns:
            Updated workflow summary dict.
        """
        data = self._read()
        wf = data["workflows"].get(workflow_id)
        if not wf:
            _error_out(f"Workflow not found: {workflow_id}", "NOT_FOUND")

        now = time.time()
        task_found = False

        for task in wf["subtasks"]:
            if task["id"] == task_id:
                task["status"] = status
                if result is not None:
                    task["result"] = result
                if session_key is not None:
                    task["session_key"] = session_key
                if status == STATUS_IN_PROGRESS and task["started_at"] is None:
                    task["started_at"] = now
                if status in TASK_TERMINAL_STATES:
                    task["completed_at"] = now
                task_found = True
                break

        if not task_found:
            _error_out(f"Task not found: {task_id} in {workflow_id}", "NOT_FOUND")

        # Update workflow-level status
        statuses = {t["status"] for t in wf["subtasks"]}
        if statuses <= TASK_TERMINAL_STATES:
            # All tasks done
            failed_count = sum(
                1 for t in wf["subtasks"] if t["status"] == STATUS_FAILED
            )
            if failed_count == len(wf["subtasks"]):
                wf["status"] = STATUS_FAILED
            else:
                wf["status"] = STATUS_COMPLETED
        elif STATUS_IN_PROGRESS in statuses or STATUS_COMPLETED in statuses:
            wf["status"] = STATUS_IN_PROGRESS
        # else remains pending

        wf["updated_at"] = now
        self._write(data)

        return self._summarize(wf)

    def get_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow.

        Args:
            workflow_id: The workflow to query.

        Returns:
            Workflow summary with progress counts.
        """
        data = self._read()
        wf = data["workflows"].get(workflow_id)
        if not wf:
            _error_out(f"Workflow not found: {workflow_id}", "NOT_FOUND")
        return self._summarize(wf)

    def aggregate_results(self, workflow_id: str) -> Dict[str, Any]:
        """Aggregate completed subtask results into a combined output.

        Collects all non-null results from completed tasks.
        Failed tasks are included with their failure status.

        Args:
            workflow_id: The workflow to aggregate.

        Returns:
            Dict with combined results, failures, and summary.
        """
        data = self._read()
        wf = data["workflows"].get(workflow_id)
        if not wf:
            _error_out(f"Workflow not found: {workflow_id}", "NOT_FOUND")

        results = []  # type: List[Dict[str, Any]]
        failures = []  # type: List[Dict[str, Any]]

        for task in wf["subtasks"]:
            if task["status"] == STATUS_COMPLETED and task["result"]:
                results.append({
                    "task_id": task["id"],
                    "label": task["label"],
                    "result": task["result"],
                })
            elif task["status"] == STATUS_FAILED:
                failures.append({
                    "task_id": task["id"],
                    "label": task["label"],
                    "result": task.get("result"),
                })

        return {
            "workflow_id": workflow_id,
            "type": wf["type"],
            "status": wf["status"],
            "completed_results": results,
            "failures": failures,
            "success_count": len(results),
            "failure_count": len(failures),
            "total_tasks": len(wf["subtasks"]),
        }

    def list_workflows(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all workflows, optionally filtering to active only.

        Args:
            active_only: If True, only return pending/in_progress workflows.

        Returns:
            List of workflow summaries.
        """
        data = self._read()
        workflows = []
        for wf in data["workflows"].values():
            if active_only and wf["status"] not in WORKFLOW_ACTIVE_STATES:
                continue
            workflows.append(self._summarize(wf))
        workflows.sort(key=lambda w: w.get("updated_at", 0), reverse=True)
        return workflows

    def cleanup(self, days: int = 7) -> int:
        """Remove completed/failed workflows older than N days.

        Args:
            days: Age threshold in days.

        Returns:
            Number of workflows removed.
        """
        data = self._read()
        cutoff = time.time() - (days * 86400)
        to_remove = []

        for wf_id, wf in data["workflows"].items():
            if wf["status"] in TASK_TERMINAL_STATES | {STATUS_CANCELLED}:
                if wf.get("updated_at", 0) < cutoff:
                    to_remove.append(wf_id)

        for wf_id in to_remove:
            del data["workflows"][wf_id]

        self._write(data)
        return len(to_remove)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _summarize(self, wf: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary dict from a full workflow record.

        Args:
            wf: Full workflow dict from the ledger.

        Returns:
            Compact summary with progress counts and elapsed time.
        """
        total = len(wf["subtasks"])
        completed = sum(1 for t in wf["subtasks"] if t["status"] == STATUS_COMPLETED)
        failed = sum(1 for t in wf["subtasks"] if t["status"] == STATUS_FAILED)
        pending = sum(1 for t in wf["subtasks"] if t["status"] == STATUS_PENDING)
        in_progress = sum(1 for t in wf["subtasks"] if t["status"] == STATUS_IN_PROGRESS)

        elapsed = time.time() - wf["created_at"]

        return {
            "workflow_id": wf["id"],
            "type": wf["type"],
            "status": wf["status"],
            "progress": f"{completed}/{total} complete",
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "failed": failed,
            "total": total,
            "elapsed_seconds": round(elapsed, 1),
            "created_at": wf["created_at"],
            "updated_at": wf["updated_at"],
            "subtasks": [
                {
                    "id": t["id"],
                    "label": t["label"],
                    "status": t["status"],
                    "session_key": t.get("session_key"),
                    "has_result": t.get("result") is not None,
                }
                for t in wf["subtasks"]
            ],
        }


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for workflow management."""
    parser = argparse.ArgumentParser(
        prog="orchestrator.py",
        description="Multi-agent workflow lifecycle manager.",
    )
    parser.add_argument("--ledger", default=None, help="Override ledger path")

    subs = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subs.add_parser("create", help="Create a new workflow")
    p_create.add_argument("--type", required=True,
                          choices=["fan_out", "pipeline", "supervisor",
                                   "expert_panel", "map_reduce"],
                          help="Orchestration pattern")
    p_create.add_argument("--subtasks", required=True,
                          help='JSON array: [{"id": "t1", "label": "..."}]')
    p_create.add_argument("--metadata", default=None,
                          help="Optional JSON metadata")

    # update
    p_update = subs.add_parser("update", help="Update a subtask status")
    p_update.add_argument("--id", required=True, help="Workflow ID")
    p_update.add_argument("--task-id", required=True, help="Subtask ID")
    p_update.add_argument("--status", required=True,
                          choices=["pending", "in_progress", "completed",
                                   "failed", "cancelled"])
    p_update.add_argument("--result", default=None, help="Result text")
    p_update.add_argument("--session-key", default=None)

    # status
    p_status = subs.add_parser("status", help="Get workflow status")
    p_status.add_argument("--id", required=True, help="Workflow ID")

    # aggregate
    p_agg = subs.add_parser("aggregate", help="Aggregate completed results")
    p_agg.add_argument("--id", required=True, help="Workflow ID")

    # list
    p_list = subs.add_parser("list", help="List workflows")
    p_list.add_argument("--active", action="store_true",
                        help="Only show active workflows")

    # cleanup
    p_clean = subs.add_parser("cleanup", help="Remove old workflows")
    p_clean.add_argument("--days", type=int, default=7)

    args = parser.parse_args()
    mgr = WorkflowManager(ledger_path=args.ledger)

    if args.command == "create":
        try:
            subtasks = json.loads(args.subtasks)
        except json.JSONDecodeError as exc:
            _error_out(f"Invalid JSON for --subtasks: {exc}", "BAD_JSON")
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                metadata = {"raw": args.metadata}

        wf_id = mgr.create_plan(args.type, subtasks, metadata)
        status = mgr.get_status(wf_id)
        _json_out({"status": "created", **status})

    elif args.command == "update":
        result = mgr.update_task(
            args.id, args.task_id, args.status,
            result=args.result,
            session_key=args.session_key,
        )
        _json_out({"status": "updated", **result})

    elif args.command == "status":
        _json_out(mgr.get_status(args.id))

    elif args.command == "aggregate":
        _json_out(mgr.aggregate_results(args.id))

    elif args.command == "list":
        workflows = mgr.list_workflows(active_only=args.active)
        _json_out({"workflows": workflows, "count": len(workflows)})

    elif args.command == "cleanup":
        removed = mgr.cleanup(days=args.days)
        _json_out({"status": "cleaned", "removed": removed})


if __name__ == "__main__":
    main()
