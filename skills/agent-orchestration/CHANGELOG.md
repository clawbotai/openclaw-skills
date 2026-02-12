# Changelog

All notable changes to the **agent-orchestration** skill are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-02-11

### Added

- **5 orchestration patterns** — Fan-Out/Fan-In, Pipeline, Supervisor/Worker, Expert Panel (Consensus), and Map-Reduce with decision tree for pattern selection
- **JSON ledger-based workflow tracking** (`memory/workflows.json`) — stateless, recoverable across session resets
- **Workflow lifecycle CLI** (`orchestrator.py`) — create, update, status, aggregate, list, cleanup commands
- **Automatic workflow status rollup** — parent workflow status derived from subtask states (all-failed → failed, any-in-progress → in_progress, all-terminal → completed)
- **Result aggregation** — collects completed subtask outputs and separates failures for synthesis by the parent agent
- **Cleanup command** — prunes completed/failed workflows older than N days
- **7 task prompt templates** (`task_templates.py`) — CodeReview, Research, DataExtraction, ConsensusCheck, Documentation, Testing, Refactor
- **Structured Output Interface** — all templates enforce `<result>...</result>` delimiters for reliable programmatic extraction
- **Result parser** (`parse_result`) — regex extraction of sub-agent output from announcement text
- **Template preview CLI** — `list` and `preview` commands for inspecting rendered prompts before spawning
- **Template dataclasses** with type-safe attributes, default values, and docstrings for each field
- **Anti-pattern documentation** — guidance on avoiding over-parallelization, context dumping, recursive orchestration, and fire-and-forget spawning
- **Cost awareness guidelines** — token impact analysis for worker count and prompt size decisions
