#!/usr/bin/env python3
"""
workflow_engine.py — Orchestrator integration layer.

Bridges shared_state (WorkItems) + skill_contract (capabilities/routing)
+ agent-orchestration (spawn/monitor) into a unified workflow engine.

The engine:
1. Accepts a high-level task description
2. Decomposes it into stages using skill contracts
3. Creates WorkItems for each stage with proper dependencies
4. Provides hooks for post-stage automation (sanity-check → reflect → lifecycle)

Usage:
    from lib.workflow_engine import WorkflowEngine

    engine = WorkflowEngine()

    # Create a pipeline workflow
    wf = engine.create_pipeline(
        name="implement-auth-refresh",
        project="mpmp",
        stages=[
            {"capability": "implement", "goal": "Build refresh token endpoint"},
            {"capability": "testing", "goal": "Write integration tests"},
            {"capability": "deploy", "goal": "Deploy to staging"},
        ],
    )

    # Start the first stage
    engine.advance(wf)

    # After a stage completes, run post-hooks and advance
    engine.run_post_hooks(wf, stage_index=0)
    engine.advance(wf)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.shared_state import (
    WorkItem, load_item, list_items, pending_hooks,
    STATE_DIR, _ensure_dirs, _now_iso, _slugify, _short_hash,
    _append_jsonl, _read_jsonl,
)
from lib.skill_contract import (
    SkillContract, load_contract, list_contracts, find_skills_for,
)

_WORKSPACE = Path(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
WORKFLOWS_DIR = _WORKSPACE / "state" / "workflows"


class WorkflowStage:
    """A single stage in a workflow pipeline."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def index(self) -> int:
        return self._data.get("index", 0)

    @property
    def capability(self) -> str:
        return self._data.get("capability", "")

    @property
    def goal(self) -> str:
        return self._data.get("goal", "")

    @property
    def skill_name(self) -> Optional[str]:
        return self._data.get("skill_name")

    @property
    def work_item_slug(self) -> Optional[str]:
        return self._data.get("work_item_slug")

    @property
    def status(self) -> str:
        return self._data.get("status", "pending")

    @property
    def post_hooks_run(self) -> bool:
        return self._data.get("post_hooks_run", False)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


class Workflow:
    """A multi-stage workflow with dependency tracking."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self._path = WORKFLOWS_DIR / f"{workflow_id}.json"
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        with open(self._path) as f:
            return json.load(f)

    def _save(self) -> None:
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def project(self) -> str:
        return self._data.get("project", "")

    @property
    def status(self) -> str:
        return self._data.get("status", "pending")

    @property
    def stages(self) -> List[WorkflowStage]:
        return [WorkflowStage(s) for s in self._data.get("stages", [])]

    @property
    def current_stage_index(self) -> int:
        return self._data.get("current_stage_index", 0)

    @property
    def post_hooks(self) -> List[str]:
        """Post-stage hook skills to run after each stage completes."""
        return self._data.get("post_hooks", ["sanity-check", "reflect", "skill-lifecycle"])

    def current_stage(self) -> Optional[WorkflowStage]:
        stages = self.stages
        idx = self.current_stage_index
        if idx < len(stages):
            return stages[idx]
        return None

    def is_complete(self) -> bool:
        return all(s.status in ("done", "skipped") for s in self.stages)

    def update_stage(self, index: int, updates: Dict[str, Any]) -> None:
        if index < len(self._data["stages"]):
            self._data["stages"][index].update(updates)
            self._save()

    def set_status(self, status: str) -> None:
        self._data["status"] = status
        self._save()

    def advance_index(self) -> None:
        self._data["current_stage_index"] = self.current_stage_index + 1
        self._save()

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def summary(self) -> str:
        stages_summary = []
        for s in self.stages:
            icon = {"pending": "⏳", "in_progress": "🔄", "done": "✅", "failed": "❌", "skipped": "⏭"}.get(s.status, "?")
            stages_summary.append(f"  {icon} {s.index}. [{s.capability}] {s.goal} → {s.skill_name or '?'} ({s.status})")
        return (
            f"Workflow: {self.name} ({self.workflow_id})\n"
            f"Project: {self.project}\n"
            f"Status: {self.status}\n"
            f"Stages:\n" + "\n".join(stages_summary)
        )


class WorkflowEngine:
    """Coordinates workflows using shared state + skill contracts."""

    def create_pipeline(
        self,
        name: str,
        project: str = "",
        stages: Optional[List[Dict[str, Any]]] = None,
        post_hooks: Optional[List[str]] = None,
    ) -> Workflow:
        """Create a new pipeline workflow.

        Args:
            name: Human-readable workflow name
            project: Project grouping
            stages: List of {"capability": str, "goal": str, "skill_name": str (optional)}
            post_hooks: Skills to run after each stage (default: sanity-check, reflect, skill-lifecycle)
        """
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        workflow_id = f"wf-{_slugify(name)}-{_short_hash(name + _now_iso())}"

        resolved_stages = []
        prev_slug = None

        for i, stage_def in enumerate(stages or []):
            cap = stage_def.get("capability", "")
            goal = stage_def.get("goal", "")
            skill_name = stage_def.get("skill_name")

            # Auto-resolve skill from capability if not specified
            if not skill_name:
                candidates = find_skills_for(capability=cap)
                if candidates:
                    skill_name = candidates[0].name

            # Create WorkItem for this stage
            slug = f"{workflow_id}-stage-{i}"
            wi = WorkItem.create(
                slug=slug,
                title=f"[{name}] Stage {i}: {goal}",
                project=project,
                goal=goal,
                assignee_skill=skill_name,
                source_task_id=workflow_id,
                author="workflow-engine",
            )

            # Wire dependency to previous stage
            if prev_slug:
                wi.add_blocker(prev_slug, author="workflow-engine")

            resolved_stages.append({
                "index": i,
                "capability": cap,
                "goal": goal,
                "skill_name": skill_name,
                "work_item_slug": slug,
                "status": "pending",
                "post_hooks_run": False,
            })

            prev_slug = slug

        wf_data = {
            "workflow_id": workflow_id,
            "name": name,
            "project": project,
            "status": "pending",
            "stages": resolved_stages,
            "current_stage_index": 0,
            "post_hooks": post_hooks or ["sanity-check", "reflect", "skill-lifecycle"],
            "created_at": _now_iso(),
        }

        wf = Workflow.__new__(Workflow)
        wf.workflow_id = workflow_id
        wf._path = WORKFLOWS_DIR / f"{workflow_id}.json"
        wf._data = wf_data
        wf._save()

        return wf

    def advance(self, wf: Workflow) -> Optional[WorkflowStage]:
        """Start the next pending stage. Returns the stage or None if all done."""
        stage = wf.current_stage()
        if not stage:
            wf.set_status("completed")
            return None

        if stage.status != "pending":
            # Already started or done, try next
            wf.advance_index()
            return self.advance(wf)

        # Check blockers
        if stage.work_item_slug:
            wi = load_item(stage.work_item_slug)
            for blocker_slug in wi.blockers:
                try:
                    blocker = load_item(blocker_slug)
                    if blocker.status not in ("done", "skipped"):
                        return None  # Still blocked
                except FileNotFoundError:
                    pass

            # Start the work item
            wi.start(assignee_skill=stage.skill_name, author="workflow-engine")

        wf.update_stage(stage.index, {"status": "in_progress"})
        if wf.status == "pending":
            wf.set_status("in_progress")

        return WorkflowStage(wf._data["stages"][stage.index])

    def complete_stage(self, wf: Workflow, stage_index: int) -> None:
        """Mark a stage as complete and update its WorkItem."""
        stages = wf._data.get("stages", [])
        if stage_index >= len(stages):
            return

        stage = stages[stage_index]
        slug = stage.get("work_item_slug")
        if slug:
            try:
                wi = load_item(slug)
                wi.complete(author="workflow-engine")
            except FileNotFoundError:
                pass

        wf.update_stage(stage_index, {"status": "done"})

        # Auto-advance
        if stage_index == wf.current_stage_index:
            wf.advance_index()

        # Check if workflow is done
        if wf.is_complete():
            wf.set_status("completed")

    def fail_stage(self, wf: Workflow, stage_index: int, reason: str = "") -> None:
        """Mark a stage as failed."""
        stages = wf._data.get("stages", [])
        if stage_index >= len(stages):
            return

        stage = stages[stage_index]
        slug = stage.get("work_item_slug")
        if slug:
            try:
                wi = load_item(slug)
                wi.fail(reason=reason, author="workflow-engine")
            except FileNotFoundError:
                pass

        wf.update_stage(stage_index, {"status": "failed"})
        wf.set_status("failed")

    def get_post_hook_tasks(self, wf: Workflow, stage_index: int) -> List[Dict[str, Any]]:
        """Generate post-hook task descriptions for a completed stage.

        Returns a list of task dicts that the orchestrator can spawn as sub-agents.
        """
        stages = wf._data.get("stages", [])
        if stage_index >= len(stages):
            return []

        stage = stages[stage_index]
        slug = stage.get("work_item_slug", "")
        tasks = []

        for hook_skill in wf.post_hooks:
            try:
                contract = load_contract(hook_skill)
            except FileNotFoundError:
                continue

            if hook_skill == "sanity-check":
                tasks.append({
                    "skill": hook_skill,
                    "description": f"Run OUTPUT gate on work item '{slug}'",
                    "inputs": {
                        "work_item_slug": slug,
                        "gate": "output",
                    },
                })
            elif hook_skill == "reflect":
                # Only trigger reflect if there are findings
                try:
                    wi = load_item(slug)
                    if wi.findings:
                        tasks.append({
                            "skill": hook_skill,
                            "description": f"Encode {len(wi.findings)} findings from '{slug}' into agent definitions",
                            "inputs": {
                                "findings": wi.findings,
                            },
                        })
                except FileNotFoundError:
                    pass
            elif hook_skill == "skill-lifecycle":
                tasks.append({
                    "skill": hook_skill,
                    "description": f"Monitor skill health after completing '{slug}'",
                    "inputs": {
                        "skill_name": stage.get("skill_name", ""),
                        "work_item_slug": slug,
                    },
                })

        return tasks

    def mark_post_hooks_run(self, wf: Workflow, stage_index: int) -> None:
        """Mark that post-hooks have been executed for a stage."""
        wf.update_stage(stage_index, {"post_hooks_run": True})


def load_workflow(workflow_id: str) -> Workflow:
    """Load an existing workflow by ID."""
    wf = Workflow(workflow_id)
    if not wf._data:
        raise FileNotFoundError(f"No workflow found: {workflow_id}")
    return wf


def list_workflows(status: Optional[str] = None) -> List[Workflow]:
    """List all workflows, optionally filtered by status."""
    if not WORKFLOWS_DIR.exists():
        return []
    workflows = []
    for f in sorted(WORKFLOWS_DIR.glob("*.json")):
        try:
            wf = Workflow(f.stem)
            if not wf._data:
                continue
            if status and wf.status != status:
                continue
            workflows.append(wf)
        except Exception:
            continue
    return workflows
