# Contributing to agent-orchestration

## Overview

This skill provides multi-agent workflow management — decomposing complex tasks into sub-agent workflows with structured templates, lifecycle tracking, and result aggregation. All state lives in a JSON ledger for crash recovery.

## File Structure

```
agent-orchestration/
├── SKILL.md              # Full usage docs: patterns, decision tree, step-by-step guide, anti-patterns
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # This file
├── _meta.json            # Skill metadata
├── scripts/
│   ├── orchestrator.py   # Workflow lifecycle: create, update, status, aggregate, list, cleanup
│   └── task_templates.py # 7 prompt templates (CodeReview, Research, etc.) + result parser
```

## Development Setup

**Requirements:** Python 3.10+ (stdlib only — no external dependencies).

```bash
python3 skills/agent-orchestration/scripts/orchestrator.py --help
python3 skills/agent-orchestration/scripts/task_templates.py --help
```

## Running Tests

No formal test suite yet. Manual verification:

```bash
# Create a workflow
python3 skills/agent-orchestration/scripts/orchestrator.py create \
  --type fan_out \
  --subtasks '[{"id": "t1", "label": "Test task 1"}, {"id": "t2", "label": "Test task 2"}]'

# Check status (use the workflow ID from create output)
python3 skills/agent-orchestration/scripts/orchestrator.py status --id <wf_id>

# Update a task
python3 skills/agent-orchestration/scripts/orchestrator.py update --id <wf_id> --task-id t1 --status completed --result "Done"

# Aggregate results
python3 skills/agent-orchestration/scripts/orchestrator.py aggregate --id <wf_id>

# List and cleanup
python3 skills/agent-orchestration/scripts/orchestrator.py list
python3 skills/agent-orchestration/scripts/orchestrator.py cleanup --days 1

# Preview templates
python3 skills/agent-orchestration/scripts/task_templates.py list
python3 skills/agent-orchestration/scripts/task_templates.py preview code_review --files "src/main.py"
```

To add automated tests, create `tests/` with pytest. Key areas:
- WorkflowManager CRUD operations and status rollup logic
- Template rendering output for each template type
- `parse_result` extraction with edge cases (missing tags, nested tags, multiline)
- Cleanup date thresholds

## Coding Standards

- **Style:** PEP 8
- **Type hints:** All function signatures annotated; use `from __future__ import annotations`
- **Docstrings:** Google-style with `Args:` and `Returns:` on every function
- **Output:** All CLI commands produce structured JSON to stdout; errors to stderr
- **Templates:** Use `@dataclass` for type-safe input; every template class needs a class-level docstring explaining its purpose and listing attribute descriptions
- **No external dependencies:** Stdlib only (json, argparse, dataclasses, textwrap, uuid)

## Making Changes

1. **New orchestration pattern** — Document in SKILL.md, add to the decision tree, no code changes needed (patterns are conceptual)
2. **New template** — Create a `@dataclass`, add a `_render_<name>` function, register in `_TEMPLATE_NAMES` and `render()`'s dispatch dict, add preview handling in `main()`
3. **Ledger schema changes** — Update `WorkflowManager` methods and class docstring; ensure backward compatibility with existing ledger files
4. **New CLI command** — Add to `main()` dispatch in the appropriate script

## PR Process

1. Branch from `main` (`feat/orchestration-...`, `fix/orchestration-...`)
2. Ensure JSON output contracts and `<result>` tag format are backward-compatible
3. Update SKILL.md if adding patterns, templates, or commands
4. Update CHANGELOG.md under `[Unreleased]`
5. Test manually with the commands above
6. Commit with conventional commits (`feat:`, `fix:`, `docs:`)
