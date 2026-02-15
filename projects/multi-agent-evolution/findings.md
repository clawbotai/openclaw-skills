# Findings & Research Log

## Schema Inspirations
- Need dual storage: append-only JSONL for git diff + agent-memory for recall. Combines benefits of file-based journaling and semantic search.
- WorkItem should encapsulate lifecycle, dependencies, telemetry, artifacts, and lessons to give orchestration + reflection a single source of truth.

## Integration Notes
- Task planner best positioned to create the initial WorkItem because it already captures intent, constraints, and project tags.
- Orchestrator can add workflow IDs + dependency edges, but actual skill execution must update lifecycle + telemetry so we need a helper module for uniform event emission.
- Hook bus (JSONL per event type) lets sanity-check / reflect subscribe without scanning entire state directory.

## Open Questions
- How much of the shared state should live in agent-memory (SQLite) vs file logs for diff-friendly git tracking?
- What minimal contract do skills need to declare so orchestrator can reason about them (inputs, outputs, side effects)?
- Should slug generation live purely in task-planner or be a helper so orchestrator can create ad-hoc work items (e.g., fan-out subtasks) without touching task planner directly?
