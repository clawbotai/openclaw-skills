# agent-orchestration

Multi-agent workflow orchestration for OpenClaw autonomous agents.

## What It Does

Provides structured patterns and tools for decomposing complex tasks into parallelizable sub-agent workflows:

- **5 orchestration patterns** — Fan-Out, Pipeline, Supervisor, Expert Panel, Map-Reduce
- **7 task templates** — Code Review, Research, Data Extraction, Consensus Check, Documentation, Testing, Refactor
- **Workflow lifecycle** — Create plan → spawn workers → track → aggregate → deliver
- **JSON ledger** — Recoverable state at `memory/workflows.json` (survives session resets)
- **Parseable output** — All templates enforce `<result>...</result>` output interface

## Quick Start

```bash
# Create a workflow
python3 skills/agent-orchestration/scripts/orchestrator.py create \
  --type fan_out \
  --subtasks '[{"id":"t1","label":"Review auth"},{"id":"t2","label":"Review API"}]'

# Check status
python3 skills/agent-orchestration/scripts/orchestrator.py status --id wf_abc123

# Update after sub-agent completes
python3 skills/agent-orchestration/scripts/orchestrator.py update \
  --id wf_abc123 --task-id t1 --status completed --result "..."

# Aggregate results
python3 skills/agent-orchestration/scripts/orchestrator.py aggregate --id wf_abc123

# Preview a task template
python3 skills/agent-orchestration/scripts/task_templates.py list
python3 skills/agent-orchestration/scripts/task_templates.py preview code_review --files "main.py"
```

## Requirements

- Python 3.9+
- No external dependencies (stdlib only)
- OpenClaw's `sessions_spawn` for actual sub-agent execution

## Architecture

```
User Request
  → Orchestrator (you) decomposes into subtasks
  → Register plan in workflows.json
  → Generate prompts via task_templates.py
  → Spawn sub-agents via sessions_spawn
  → Track via orchestrator.py update
  → Aggregate via orchestrator.py aggregate
  → Deliver synthesized result to user
```

See `SKILL.md` for the complete orchestration playbook.
