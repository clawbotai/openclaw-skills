# Shared State Schema & API Proposal

## Objectives
1. Give every software-development skill a common contract for publishing work state, artifacts, metrics, and lessons.
2. Enable the orchestrator + task planner to reason about dependencies, ownership, and readiness.
3. Provide automatic hooks for sanity-check → reflect → skill-lifecycle after each stage.

## Data Model Overview
```
WorkItem (root)
├── identity: slug, title, source_task_id
├── intent: goal, success_criteria, constraints
├── lifecycle: status, assignee_skill, timestamps
├── dependencies: blockers[], dependents[]
├── telemetry: metrics[], tests[], logs[]
├── artifacts: files[], links[], docs[]
├── lessons: findings[], followups[]
└── history: events[]
```
Each field is JSON-serializable; we store it both in agent-memory (for search) and as append-only JSONL under `state/work_items/<slug>.jsonl` for git visibility.

### Minimal JSON Schema (YAML notation)
```yaml
WorkItem:
  slug: str  # e.g. "backend-api-auth-refresh"
  title: str
  source_task_id: str  # maps back to task-planner ID
  project: str  # optional grouping (torr-statics, mpmp, etc.)
  intent:
    goal: str
    success_criteria: [str]
    constraints: [str]
  lifecycle:
    status: enum[todo|in_progress|blocked|review|done|failed]
    assignee_skill: str  # python-backend, devops, docs-engine, etc.
    orchestrator_workflow: str  # optional workflow id
    timestamps:
      created_at: iso8601
      started_at: iso8601
      completed_at: iso8601
  dependencies:
    blockers: [slug]
    dependents: [slug]
  telemetry:
    metrics: [Metric]
    tests: [TestRun]
    logs: [LogRef]
  artifacts:
    files: [Artifact]
    links: [Artifact]
    docs: [Artifact]
  lessons:
    findings: [str]
    followups: [str]
  history: [Event]

Metric:
  name: str
  value: number|string
  unit: str
  timestamp: iso8601
  context: str

TestRun:
  name: str
  status: enum[pass|fail|error|skip]
  evidence: str  # path or summary
  timestamp: iso8601

Artifact:
  type: enum[file|diagram|link|doc]
  label: str
  path: str  # relative path or URL
  hash: str  # optional for integrity
  metadata: dict

Event:
  type: enum[created|status_change|dependency_added|artifact_added|metric_recorded|handoff]
  author: str  # skill or agent id
  timestamp: iso8601
  payload: dict
```

## Storage Strategy
| Layer | Purpose | Tech |
|-------|---------|------|
| Append-only JSONL (`state/work_items/<slug>.jsonl`) | Full history, git diffable, human-readable | Filesystem |
| Agent Memory (`agent-memory` skill) | Fast lookup, semantic recall | SQLite + embeddings |
| Task Planner link (`.nlplanner/projects/...`) | Human dashboard | Markdown backlink |

When a skill updates a work item:
1. Write event to JSONL.
2. Upsert summary row into agent-memory (`kind=work_item`).
3. Update task-planner task status/notes (optional but encouraged).

Provide helper module `lib/shared_state.py` with functions:
```python
from datetime import datetime
from pathlib import Path
from typing import Dict

STATE_DIR = Path("state/work_items")

class SharedState:
    def __init__(self, slug: str): ...
    def load(self) -> Dict: ...
    def append_event(self, event_type: str, payload: Dict): ...
    def update_lifecycle(self, status: str, assignee: str = None): ...
    def add_artifact(self, artifact: Dict): ...
    def record_metric(self, metric: Dict): ...
```
Helper automatically handles timestamps, ensures file exists, and calls hooks (agent-memory upsert + optional task-planner sync).

## Skill Responsibilities
| Skill | Responsibilities |
|-------|------------------|
| task-planner | Creates initial WorkItem entry when a task is captured. Adds `source_task_id`, `intent`, `project`, dependencies. |
| agent-orchestration | Updates `lifecycle.status` as workflows spawn/complete. Writes `history` events referencing workflow ID. |
| python-backend / devops / docs-engine | On start: `update_lifecycle(status="in_progress", assignee_skill="python-backend")`. On completion: add artifacts + metrics → set status to `review` or `done`. |
| agent-memory | Provides `remember_work_item(work_item_dict)` API for indexing. |
| sanity-check | Reads telemetry/tests to decide gating. Writes `lessons.followups` if issues found. |
| reflect | Consumes `lessons.findings` + event stream to update SOUL/TOOLS. |
| skill-lifecycle | Monitors events for failures, auto-opens repair tasks referencing `slug`. |

## Hooks & Automation
- `after_event` hook chain: `[memory_indexer, task_planner_sync, hook_bus]`
- Hook bus publishes to `hooks/<event_type>.jsonl` so sanity-check/reflect subscribe without polling entire state.
- Standard event names: `created`, `started`, `artifact_added`, `test_recorded`, `metrics_recorded`, `blocked`, `unblocked`, `handoff`, `completed`, `failed`.

## Adoption Plan
1. **Create shared_state helper module** under `lib/shared_state/` with tests.
2. **Add CLI** `bin/shared-state` for manual inspection (`list`, `show`, `tail`, `graph dependencies`).
3. **Retrofit** python-backend + devops to use helper (Phase 3 reference implementations).
4. **Update orchestrator** to auto-create WorkItem entries for each workflow subtask and propagate dependencies.
5. **Document** contract in `docs/multi-agent/shared-state.md` for all skill authors.

## File Layout
```
state/
  work_items/
    backend-api-auth-refresh.jsonl
    devops-ci-hardening.jsonl
  hooks/
    completed.jsonl
    failed.jsonl
```
Each JSONL entry is a single event record:
```json
{"slug":"backend-api-auth-refresh","event":"artifact_added","timestamp":"2026-02-14T20:45:00Z","payload":{"artifact":{"type":"file","label":"auth_flow.md","path":"docs/auth_flow.md","hash":"..."}}}
```

## Sample Workflow
1. Task planner logs "Implement refresh token endpoint" → creates slug `backend-refresh-endpoint`.
2. Orchestrator spawns pipeline `design → implement → test`. Each step writes `started`/`completed` events.
3. python-backend skill adds artifacts (code paths) + metrics (coverage%) + tests.
4. devops skill records deployment test results.
5. sanity-check listens to `completed` events → runs gating. If pass, updates status to `done`; if fail, writes `lessons.followups` and sets status `failed`.
6. reflect ingests `lessons` entries nightly and updates SOUL/TOOLS.

## Open Items
- Decide on slug generation algorithm (task planner vs orchestrator). Recommendation: `project-shortname + concise slug + 4-char hash`.
- Determine retention/rotation policy (default keep all, optional prune via CLI).
- Align with agent-memory schema (`memory/*.md` vs DB). Provide migration script.
```
python3 scripts/shared_state/bootstrap.py --import-nlplanner
```

## Next Steps
- [ ] Build `lib/shared_state.py` with load/append helpers.
- [ ] Create `bin/shared-state` inspection CLI.
- [ ] Wire task-planner capture flow to instantiate WorkItem files.
- [ ] Retrofit python-backend + devops as reference implementations.
- [ ] Update orchestrator + documentation.
```
