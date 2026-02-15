#!/usr/bin/env python3
"""
shared_state.py — Shared state for multi-agent skill coordination.

Provides a WorkItem abstraction with append-only JSONL storage,
agent-memory indexing, and event hooks for sanity-check/reflect/lifecycle.

Usage:
    from lib.shared_state import WorkItem, list_items, load_item

    # Create
    wi = WorkItem.create(
        slug="backend-refresh-endpoint",
        title="Implement refresh token endpoint",
        project="mpmp",
        goal="Add JWT refresh flow",
        success_criteria=["Tests pass", "Token rotation works"],
        assignee_skill="python-backend",
        source_task_id="task-042",
    )

    # Update lifecycle
    wi.start()
    wi.add_artifact({"type": "file", "label": "auth.py", "path": "src/auth.py"})
    wi.record_metric({"name": "test_coverage", "value": 87, "unit": "%"})
    wi.record_test({"name": "test_refresh", "status": "pass"})
    wi.add_finding("Refresh tokens should expire in 7 days, not 30")
    wi.complete()

    # Load existing
    wi = load_item("backend-refresh-endpoint")
    print(wi.status, wi.artifacts)

    # List all
    for item in list_items(status="in_progress"):
        print(item.slug, item.title)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve workspace root
_WORKSPACE = Path(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
STATE_DIR = _WORKSPACE / "state" / "work_items"
HOOKS_DIR = _WORKSPACE / "state" / "hooks"

# Valid statuses
STATUSES = ("todo", "in_progress", "blocked", "review", "done", "failed")

# Valid event types
EVENT_TYPES = (
    "created", "started", "status_change", "dependency_added",
    "artifact_added", "metric_recorded", "test_recorded",
    "finding_added", "followup_added", "handoff", "completed", "failed",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    """Generate a filesystem-safe slug from text."""
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s[:80]


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:6]


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    """Append a single JSON record to a JSONL file."""
    with open(path, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read all records from a JSONL file."""
    if not path.exists():
        return []
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def _publish_hook(event_type: str, event: Dict[str, Any]) -> None:
    """Write event to hook bus (hooks/<event_type>.jsonl)."""
    _ensure_dirs()
    hook_file = HOOKS_DIR / f"{event_type}.jsonl"
    _append_jsonl(hook_file, event)


def _index_to_memory(work_item: "WorkItem") -> None:
    """Best-effort upsert into agent-memory for semantic recall."""
    try:
        from lib.memory_client import remember
        summary = (
            f"[work_item:{work_item.slug}] {work_item.title} "
            f"| status={work_item.status} "
            f"| skill={work_item.assignee_skill or 'unassigned'} "
            f"| project={work_item.project or 'none'}"
        )
        remember(summary, importance=0.6, memory_type="semantic")
    except Exception:
        pass  # Memory indexing is best-effort


class WorkItem:
    """A unit of tracked work flowing through the multi-agent system."""

    def __init__(self, slug: str):
        self.slug = slug
        self._path = STATE_DIR / f"{slug}.jsonl"
        self._data = self._rebuild_state()

    def _rebuild_state(self) -> Dict[str, Any]:
        """Rebuild current state by replaying all events."""
        events = _read_jsonl(self._path)
        if not events:
            return {}

        state = {
            "slug": self.slug,
            "title": "",
            "project": "",
            "source_task_id": "",
            "intent": {"goal": "", "success_criteria": [], "constraints": []},
            "lifecycle": {
                "status": "todo",
                "assignee_skill": None,
                "orchestrator_workflow": None,
                "timestamps": {},
            },
            "dependencies": {"blockers": [], "dependents": []},
            "telemetry": {"metrics": [], "tests": [], "logs": []},
            "artifacts": [],
            "lessons": {"findings": [], "followups": []},
            "history": events,
        }

        for ev in events:
            etype = ev.get("event", "")
            payload = ev.get("payload", {})
            ts = ev.get("timestamp", "")

            if etype == "created":
                state["title"] = payload.get("title", "")
                state["project"] = payload.get("project", "")
                state["source_task_id"] = payload.get("source_task_id", "")
                state["intent"] = payload.get("intent", state["intent"])
                state["lifecycle"]["assignee_skill"] = payload.get("assignee_skill")
                state["lifecycle"]["timestamps"]["created_at"] = ts
                if payload.get("status"):
                    state["lifecycle"]["status"] = payload["status"]
            elif etype == "started":
                state["lifecycle"]["status"] = "in_progress"
                state["lifecycle"]["timestamps"]["started_at"] = ts
                if payload.get("assignee_skill"):
                    state["lifecycle"]["assignee_skill"] = payload["assignee_skill"]
            elif etype == "status_change":
                state["lifecycle"]["status"] = payload.get("status", state["lifecycle"]["status"])
                if payload.get("status") == "done":
                    state["lifecycle"]["timestamps"]["completed_at"] = ts
            elif etype == "completed":
                state["lifecycle"]["status"] = "done"
                state["lifecycle"]["timestamps"]["completed_at"] = ts
            elif etype == "failed":
                state["lifecycle"]["status"] = "failed"
                state["lifecycle"]["timestamps"]["completed_at"] = ts
            elif etype == "artifact_added":
                art = payload.get("artifact", {})
                if art:
                    state["artifacts"].append(art)
            elif etype == "metric_recorded":
                m = payload.get("metric", {})
                if m:
                    state["telemetry"]["metrics"].append(m)
            elif etype == "test_recorded":
                t = payload.get("test", {})
                if t:
                    state["telemetry"]["tests"].append(t)
            elif etype == "finding_added":
                f = payload.get("finding", "")
                if f:
                    state["lessons"]["findings"].append(f)
            elif etype == "followup_added":
                f = payload.get("followup", "")
                if f:
                    state["lessons"]["followups"].append(f)
            elif etype == "dependency_added":
                dep = payload.get("dependency", {})
                if dep.get("blocker"):
                    bl = dep["blocker"]
                    if bl not in state["dependencies"]["blockers"]:
                        state["dependencies"]["blockers"].append(bl)
                if dep.get("dependent"):
                    d = dep["dependent"]
                    if d not in state["dependencies"]["dependents"]:
                        state["dependencies"]["dependents"].append(d)
            elif etype == "handoff":
                if payload.get("to_skill"):
                    state["lifecycle"]["assignee_skill"] = payload["to_skill"]
                if payload.get("workflow_id"):
                    state["lifecycle"]["orchestrator_workflow"] = payload["workflow_id"]

        return state

    def _emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None, author: str = "agent") -> Dict[str, Any]:
        """Emit an event: write to JSONL, publish hook, index memory."""
        _ensure_dirs()
        event = {
            "slug": self.slug,
            "event": event_type,
            "timestamp": _now_iso(),
            "author": author,
            "payload": payload or {},
        }
        _append_jsonl(self._path, event)
        _publish_hook(event_type, event)
        # Rebuild state after event
        self._data = self._rebuild_state()
        # Best-effort memory indexing on significant events
        if event_type in ("created", "completed", "failed", "handoff"):
            _index_to_memory(self)
        return event

    # ── Properties ──

    @property
    def title(self) -> str:
        return self._data.get("title", "")

    @property
    def project(self) -> str:
        return self._data.get("project", "")

    @property
    def source_task_id(self) -> str:
        return self._data.get("source_task_id", "")

    @property
    def status(self) -> str:
        return self._data.get("lifecycle", {}).get("status", "todo")

    @property
    def assignee_skill(self) -> Optional[str]:
        return self._data.get("lifecycle", {}).get("assignee_skill")

    @property
    def artifacts(self) -> List[Dict]:
        return self._data.get("artifacts", [])

    @property
    def metrics(self) -> List[Dict]:
        return self._data.get("telemetry", {}).get("metrics", [])

    @property
    def tests(self) -> List[Dict]:
        return self._data.get("telemetry", {}).get("tests", [])

    @property
    def findings(self) -> List[str]:
        return self._data.get("lessons", {}).get("findings", [])

    @property
    def followups(self) -> List[str]:
        return self._data.get("lessons", {}).get("followups", [])

    @property
    def blockers(self) -> List[str]:
        return self._data.get("dependencies", {}).get("blockers", [])

    @property
    def dependents(self) -> List[str]:
        return self._data.get("dependencies", {}).get("dependents", [])

    @property
    def history(self) -> List[Dict]:
        return self._data.get("history", [])

    @property
    def timestamps(self) -> Dict[str, str]:
        return self._data.get("lifecycle", {}).get("timestamps", {})

    @property
    def data(self) -> Dict[str, Any]:
        return dict(self._data)

    # ── Lifecycle ──

    @classmethod
    def create(
        cls,
        slug: Optional[str] = None,
        title: str = "",
        project: str = "",
        goal: str = "",
        success_criteria: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        assignee_skill: Optional[str] = None,
        source_task_id: str = "",
        author: str = "agent",
    ) -> "WorkItem":
        """Create a new WorkItem and emit 'created' event."""
        if not slug:
            base = _slugify(title or "untitled")
            slug = f"{project + '-' if project else ''}{base}-{_short_hash(title + _now_iso())}"

        wi = cls.__new__(cls)
        wi.slug = slug
        wi._path = STATE_DIR / f"{slug}.jsonl"
        wi._data = {}

        if wi._path.exists():
            raise FileExistsError(f"WorkItem '{slug}' already exists at {wi._path}")

        wi._emit("created", {
            "title": title,
            "project": project,
            "source_task_id": source_task_id,
            "assignee_skill": assignee_skill,
            "intent": {
                "goal": goal,
                "success_criteria": success_criteria or [],
                "constraints": constraints or [],
            },
            "status": "todo",
        }, author=author)

        return wi

    def start(self, assignee_skill: Optional[str] = None, author: str = "agent") -> None:
        """Transition to in_progress."""
        payload = {}
        if assignee_skill:
            payload["assignee_skill"] = assignee_skill
        self._emit("started", payload, author=author)

    def complete(self, author: str = "agent") -> None:
        """Transition to done."""
        self._emit("completed", {}, author=author)

    def fail(self, reason: str = "", author: str = "agent") -> None:
        """Transition to failed."""
        self._emit("failed", {"reason": reason}, author=author)

    def set_status(self, status: str, author: str = "agent") -> None:
        """Set arbitrary status."""
        if status not in STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {STATUSES}")
        self._emit("status_change", {"status": status}, author=author)

    def handoff(self, to_skill: str, workflow_id: Optional[str] = None, author: str = "agent") -> None:
        """Hand off to another skill."""
        self._emit("handoff", {
            "to_skill": to_skill,
            "workflow_id": workflow_id,
        }, author=author)

    # ── Artifacts ──

    def add_artifact(self, artifact: Dict[str, Any], author: str = "agent") -> None:
        """Record a produced artifact (file, link, doc, diagram)."""
        self._emit("artifact_added", {"artifact": artifact}, author=author)

    # ── Telemetry ──

    def record_metric(self, metric: Dict[str, Any], author: str = "agent") -> None:
        """Record a metric (coverage, latency, LOC, etc.)."""
        if "timestamp" not in metric:
            metric["timestamp"] = _now_iso()
        self._emit("metric_recorded", {"metric": metric}, author=author)

    def record_test(self, test: Dict[str, Any], author: str = "agent") -> None:
        """Record a test result."""
        if "timestamp" not in test:
            test["timestamp"] = _now_iso()
        self._emit("test_recorded", {"test": test}, author=author)

    # ── Dependencies ──

    def add_blocker(self, blocker_slug: str, author: str = "agent") -> None:
        """Add a blocking dependency."""
        self._emit("dependency_added", {
            "dependency": {"blocker": blocker_slug}
        }, author=author)

    def add_dependent(self, dependent_slug: str, author: str = "agent") -> None:
        """Add a downstream dependent."""
        self._emit("dependency_added", {
            "dependency": {"dependent": dependent_slug}
        }, author=author)

    # ── Lessons ──

    def add_finding(self, finding: str, author: str = "agent") -> None:
        """Record a lesson learned / finding."""
        self._emit("finding_added", {"finding": finding}, author=author)

    def add_followup(self, followup: str, author: str = "agent") -> None:
        """Record a follow-up action needed."""
        self._emit("followup_added", {"followup": followup}, author=author)

    # ── Serialization ──

    def summary(self) -> str:
        """One-line summary for listing."""
        age = ""
        created = self.timestamps.get("created_at", "")
        if created:
            age = created[:10]
        return f"[{self.status:12s}] {self.slug}  ({self.assignee_skill or 'unassigned'})  {age}"

    def to_dict(self) -> Dict[str, Any]:
        """Full state as dict (excluding raw history for compactness)."""
        d = dict(self._data)
        d.pop("history", None)
        return d

    def __repr__(self) -> str:
        return f"<WorkItem slug={self.slug!r} status={self.status!r}>"


# ── Module-Level Helpers ──

def load_item(slug: str) -> WorkItem:
    """Load an existing WorkItem by slug."""
    wi = WorkItem(slug)
    if not wi._data:
        raise FileNotFoundError(f"No WorkItem found for slug '{slug}'")
    return wi


def list_items(
    status: Optional[str] = None,
    project: Optional[str] = None,
    skill: Optional[str] = None,
) -> List[WorkItem]:
    """List all WorkItems, optionally filtered."""
    _ensure_dirs()
    items = []
    for f in sorted(STATE_DIR.glob("*.jsonl")):
        slug = f.stem
        try:
            wi = WorkItem(slug)
            if not wi._data:
                continue
            if status and wi.status != status:
                continue
            if project and wi.project != project:
                continue
            if skill and wi.assignee_skill != skill:
                continue
            items.append(wi)
        except Exception:
            continue
    return items


def dependency_graph() -> Dict[str, Dict[str, List[str]]]:
    """Build a dependency graph of all work items.

    Returns:
        Dict mapping slug → {"blockers": [...], "dependents": [...]}
    """
    items = list_items()
    graph = {}
    for wi in items:
        graph[wi.slug] = {
            "blockers": list(wi.blockers),
            "dependents": list(wi.dependents),
        }
    return graph


def pending_hooks(event_type: str, since: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read hook events, optionally filtered by timestamp."""
    hook_file = HOOKS_DIR / f"{event_type}.jsonl"
    events = _read_jsonl(hook_file)
    if since:
        events = [e for e in events if e.get("timestamp", "") > since]
    return events
