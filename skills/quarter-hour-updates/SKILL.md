---
name: quarter-hour-updates
description: Provides structured progress updates every 15 minutes (at :00, :15, :30, :45) while a task is running. Each update includes a short synopsis plus the next two planned steps, stays under 150 words, and continues until the user marks the task complete.
version: "2.1.0"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - WebFetch
  - WebSearch
  - Exec
---

# Quarter-Hour Update Skill

## Overview
This skill ships a working scheduler that emits concise updates every quarter hour. It integrates with planning-with-files, natural-language-planner, reflect-learn, and agent-observability-dashboard so every update is measurable and auditable.

By default (verification mode) the skill runs every **120 seconds**; adjust `--interval-seconds` to 900 for production quarter-hour cadence. Updates always include:
1. **Synopsis** (≤150 words) describing work since the previous checkpoint.
2. **Next two steps** from the current development plan.
3. Automatic logging to `progress.md`, `data/updates.log`, and the observability dashboard.

## Folder Structure
```
skills/quarter-hour-updates/
├── SKILL.md
├── data/
│   └── state.json
├── scripts/
    ├── state.py
    ├── start_task.py
    ├── stop_task.py
    ├── log_progress.py
    └── daemon.py
```

## Command Cheatsheet
| Action | Command |
|--------|---------|
| Start updates | `python skills/quarter-hour-updates/scripts/start_task.py "<task name>" "<description>" [--plan ... --progress ... --findings ...]` |
| Record progress | `python skills/quarter-hour-updates/scripts/log_progress.py --synopsis "..." --next "step one" --next "step two"` |
| Stop updates | `python skills/quarter-hour-updates/scripts/stop_task.py` |

The start script spins up a background daemon (pid stored in `data/daemon.pid`) that waits for the next real quarter-hour tick and then posts updates until stopped.

## Workflow
1. **Kickoff**
   - Update `progress.md`/`findings.md` per planning-with-files.
   - Run `start_task.py` to register the task and start the daemon (log entry recorded in observability dashboard).
2. **While Working**
   - Whenever new progress occurs, call `log_progress.py` with a synopsis and the next two steps (they will be used at the upcoming quarter-hour update).
   - The daemon enforces the 150-word limit and appends formatted updates to `progress.md` + `data/updates.log`.
3. **Completion / Pause**
   - Run `stop_task.py` to halt updates. This persists final status and cancels the timer loop.

## Observability & Guardrails
- Every update appends to `progress.md` and `data/updates.log`, and the daemon prints the entry so it can be relayed to the user immediately.
- Telemetry payload `{timestamp, task_name, summary_hash, next_steps}` must be pushed to agent-observability-dashboard alongside each update.
- If the daemon misses a scheduled tick, it prints a warning; notify the user and immediately reschedule.
- Zero-trust: never include sensitive data in the synopsis. If sensitive info is required, reference the secure log entry instead.

## Testing
- For full validation, run `start_task.py` and leave the daemon active for at least 45 minutes (four updates). Use `log_progress.py` before each quarter-hour to feed fresh content. Confirm:
  1. Updates arrive at :00/:15/:30/:45.
  2. Each synopsis is ≤150 words and includes next steps.
  3. Logs/telemetry capture every event.
- For faster dry-runs, pass `--simulation-speed 60` to `start_task.py` to simulate 1 second = 1 minute. **Real deployments must use the default speed (1.0).**

## Failure Handling
- **Missed update:** notify user, log incident, and keep the daemon running for the next tick.
- **Task paused:** stop daemon, log PAUSED status in `progress.md`, retain state for later resumption.
- **Task complete:** issue a final summary update, stop daemon, archive `data/state.json` snapshot into findings.
