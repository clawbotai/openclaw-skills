# Multi-Agent Software Evolution Plan

## Goal
Create an interdependent software-development agent stack where skills share structured state, call each other through explicit contracts, and trigger automatic reflection/evolution loops after work completes.

## Success Criteria
- Shared state schema documented and adopted by all software-dev skills (python-backend, devops, docs-engine, product-management, task-planner, agent-memory).
- Orchestrator workflow can route tasks across skills using contracts + dependencies, updating shared state as tasks progress.
- Automatic post-task hooks trigger sanity-check, reflect, and skill-lifecycle with captured telemetry.
- Documentation + examples demonstrate end-to-end flow.

## Phases

### Phase 1 — Current-State Inventory & Requirements
- Audit existing skills (python-backend, devops, docs-engine, agent-orchestration, agent-memory, task-planner, reflect, skill-lifecycle).
- Capture current inputs/outputs, state handling, and integration gaps.
- Produce requirements doc for shared state + orchestration.

### Phase 2 — Shared State Schema & APIs
- Design a JSON/YAML schema covering task metadata, artifacts, metrics, and lessons.
- Specify storage (agent-memory + file logs) and access API (Python helper module + CLI contract).
- Provide migration guidance for each skill.

### Phase 3 — Skill Retrofits & Contracts
- Implement shared state helpers in at least two core skills (python-backend, devops) as reference implementations.
- Document contract patterns (e.g., `plan → implement → test → deploy`).
- Update task-planner to auto-tag tasks with skill + dependency metadata.

### Phase 4 — Orchestrator Workflow & Supervisor Logic
- Extend agent-orchestration skill with workflow graph + dependency resolution.
- Enable skills to invoke downstream steps via orchestrator RPC (or structured task handoffs).
- Ensure orchestrator records progress in shared state.

### Phase 5 — Evolution Loop Automation
- Wire sanity-check, reflect, and skill-lifecycle to run after each workflow stage.
- Capture telemetry + lessons, feed them back into SOUL/TOOLS/memory files.
- Define safeguards + escalation rules (retry policy, user notification).

## Tracking
- Use `progress.md` for chronological updates.
- Use `findings.md` for insights, schema drafts, open questions.
- Update this plan as phases complete or scope shifts.
