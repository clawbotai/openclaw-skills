---
name: agent-orchestration
description: Multi-agent coordination — task routing, handoff protocols, fan-out/fan-in patterns, and supervisor workflows for complex multi-step operations.
---

# agent-orchestration — Multi-Agent Workflow Playbook

## Why This Exists

Some tasks exceed what a single agent can do well in one session. A 30-skill documentation sweep, a multi-domain deal review, a full incident response — these require decomposition into parallel or sequential work streams. But naive parallelism creates chaos. Sub-agents share no memory with you or each other. They can't ask clarifying questions. They don't know what the other workers are doing. Without structure, you get redundant work, incompatible outputs, and silent failures.

This skill provides that structure: five proven patterns for decomposing work, a tracking ledger so nothing gets lost, task templates so sub-agents get exactly the context they need (and no more), and failure recovery protocols for when things go wrong. You are the **Orchestrator** — you plan, spawn, monitor, and synthesize. The patterns keep you from reinventing coordination logic every time.

---

## The 5 Patterns

### 1. Fan-Out / Fan-In (Parallel)

**When:** Multiple independent subtasks with no data dependencies between them.

```
You (Orchestrator)
  ├── spawn Worker A (batch 1)
  ├── spawn Worker B (batch 2)
  ├── spawn Worker C (batch 3)
  └── collect all results → synthesize
```

**Example:** "Document all 30 skills" → 5 workers, 6 skills each.
**Sweet spot:** 3–6 parallel workers. Each runs 5–15 min. More than 6 causes resource contention and monitoring overhead that exceeds the parallelism benefit.

### 2. Pipeline (Sequential)

**When:** Each step depends on the previous step's output.

```
You → spawn Step 1 → get result → spawn Step 2(result) → get result → Step 3(result) → done
```

**Example:** "Research → outline → draft → review → publish"
**Key:** Pass ONLY the needed output between stages. If you pass everything, later stages drown in irrelevant context.

### 3. Supervisor / Worker

**When:** Complex task needing ongoing coordination and judgment calls mid-stream.

```
You (Supervisor)
  ├── spawn Worker (specific piece)
  ├── review result → decide next step
  ├── spawn another Worker (next piece)
  ├── handle failure → reassign or retry
  └── synthesize final deliverable
```

**Example:** "Build and deploy a web app"
**Key:** YOU are the supervisor. Don't spawn a supervisor.

### 4. Expert Panel (Consensus)

**When:** Decision quality matters more than speed. Multiple perspectives needed.

```
You → spawn Security Expert
    → spawn Performance Expert
    → spawn Architecture Expert
    → collect all opinions → synthesize consensus
```

**Example:** "Review this system design for production readiness"
**Key:** Give each expert a distinct `expert_role`. Use ConsensusCheckTemplate.

### 5. Map-Reduce

**When:** Large dataset needs processing then aggregation.

```
Map:    You → spawn N workers (each processes a partition)
Reduce: You → collect all outputs → aggregate into final result
```

**Example:** "Analyze all skill scripts for comment quality"
**Key:** Partition data evenly. The reduce step is YOUR job — don't spawn for it.

---

## Decision Tree: Which Pattern?

```
Is the task a single unit of work (<5 min)?
  YES → Don't orchestrate. Do it inline.
  NO  ↓

Are subtasks independent (no data dependencies)?
  YES → Fan-Out
  NO  ↓

Does each step need the previous step's output?
  YES → Pipeline
  NO  ↓

Do you need multiple expert opinions?
  YES → Expert Panel
  NO  ↓

Is it a large dataset needing processing + aggregation?
  YES → Map-Reduce
  NO  ↓

Is it complex with ongoing judgment needed?
  YES → Supervisor
```

**Rule of thumb:** <5 minutes → inline. 5–15 minutes → maybe orchestrate. >15 minutes → definitely orchestrate.

---

## Context Minimization — The #1 Orchestration Skill

Sub-agents share **no memory** with you. No conversation history, no file state, no implicit knowledge. Everything they need must be in the task prompt, and everything they don't need wastes tokens and creates confusion.

This is the single most common source of orchestration failures. Not pattern selection, not monitoring — context.

### What to Include

- **The specific task** — one sentence, unambiguous
- **Input data** — the actual content to work on (not a file path they can't access)
- **Constraints** — time limits, scope boundaries, don't-touch rules
- **Output format** — exact structure (JSON schema preferred) with `<result>` wrapper tags
- **Role** — one sentence establishing expertise

### What to Exclude

- Your conversation history with the user
- Other subtasks' descriptions (they don't need to know)
- Project-wide context unrelated to their specific task
- Explanations of why you're orchestrating

### The Context Budget

Every word in a task prompt costs tokens across every sub-agent that receives it. 500 words × 5 workers = 2500 words of prompt cost. 2000 words × 10 workers = 20,000 words. Trim ruthlessly. If a sub-agent doesn't need a piece of information to complete its specific task, cut it.

---

## Anti-Patterns

### The Context Dump

**Pattern:** Pasting your entire conversation, project README, and multiple file contents into every sub-agent's task prompt.

**Reality:** Sub-agents drown in irrelevant context. They latch onto wrong details. Token costs multiply. Responses get unfocused because the agent can't determine what matters.

**Fix:** Write task prompts from scratch for each sub-agent. Include only what's needed for their specific subtask. If you can't summarize the needed context in under 500 words, the task isn't decomposed enough.

### The Recursive Dream

**Pattern:** Designing workflows where sub-agents spawn their own sub-agents.

**Reality:** Sub-agents cannot spawn sub-agents (single depth enforced by the platform). Even if they could, recursive orchestration creates untraceable execution trees, duplicated work, and impossible failure recovery.

**Fix:** All decomposition happens at your level. If a subtask is too complex for one sub-agent, break it into smaller subtasks in YOUR plan. You are the only orchestrator.

### Fire and Forget

**Pattern:** Spawning sub-agents without tracking them in the ledger. Assuming they'll complete. Moving on.

**Reality:** Sub-agents fail silently. They time out. They produce malformed output. Without tracking, you discover this only when the user asks "where are my results?" and you have no answer.

**Fix:** Always use the orchestrator ledger. Update status on spawn, on completion, on failure. Check `orchestrator.py status` periodically. For workflows >10 minutes, give the user a progress update.

### The Monolith Spawn

**Pattern:** Creating one giant sub-agent with a massive task instead of decomposing into multiple focused workers.

**Reality:** A single sub-agent with a 30-minute task and 2000-word prompt is just a slower, less reliable version of doing it yourself. It gets no parallelism benefit and has a single point of failure.

**Fix:** If the task prompt exceeds ~500 words or the expected runtime exceeds ~15 minutes, decompose further. Each sub-agent should have one clear deliverable.

---

## Failure Recovery

Orchestration failures are not exceptions — they're expected. Plan for them.

### Single Worker Failure

```
Worker times out or returns error
  → Update ledger: status=failed, result=<error>
  → Retry with error context in prompt (max 2 retries)
  → If retry fails → mark as failed, continue with other workers
  → Note the gap in final synthesis
```

### Multiple Worker Failure (≥3 in same workflow)

```
3+ subtasks failed
  → STOP spawning new workers
  → Aggregate what succeeded
  → Report to user: "X of Y tasks completed. Failed tasks: [list]. Partial results available."
  → Ask user whether to retry failed tasks, adjust approach, or accept partial results
```

### Whole Workflow Stall

```
No workers completing for >2× expected runtime
  → Check sessions_list for running sub-agents
  → If agents are running → likely slow, not stuck. Wait longer.
  → If agents have terminated with no result → ledger is stale. 
  → Collect whatever results exist
  → Report to user with honest assessment
```

### Cascade Failure in Pipelines

```
Pipeline step N fails
  → Steps N+1, N+2, ... cannot proceed (they depend on N's output)
  → Retry step N (max 2 retries with error context)
  → If retry fails → report to user with results from steps 1 through N-1
  → Never skip a pipeline step or fabricate intermediate output
```

---

## Operational Guide

### Step 1: Decompose

Break the request into discrete subtasks. For each, determine: Can it run in parallel? What's the minimum context needed? What does "done" look like?

### Step 2: Register the Plan

```bash
python3 skills/agent-orchestration/scripts/orchestrator.py create \
  --type fan_out \
  --subtasks '[{"id":"t1","label":"Review auth"},{"id":"t2","label":"Review API"},{"id":"t3","label":"Review data"}]'
```

Returns a `workflow_id`.

### Step 3: Generate Task Prompts

```bash
python3 skills/agent-orchestration/scripts/task_templates.py preview code_review --files "src/auth.py"
```

Each template produces a self-contained prompt with Role, Task, Constraints, Output Format, and Output Interface sections.

### Step 4: Spawn

```
sessions_spawn(task=<rendered prompt>, label="wf_<id>_<task>_<desc>", runTimeoutSeconds=600)
```

Update ledger: `orchestrator.py update --id X --task-id Y --status in_progress --session-key <key>`

### Step 5: Monitor

```bash
python3 skills/agent-orchestration/scripts/orchestrator.py status --id <workflow_id>
```

Also `sessions_list` to check running agents. For >10 min workflows, update the user.

### Step 6: Collect

Sub-agents wrap output in `<result>...</result>` tags. Parse and update ledger with `--status completed --result "<output>"`.

### Step 7: Aggregate

```bash
python3 skills/agent-orchestration/scripts/orchestrator.py aggregate --id <workflow_id>
```

Synthesize into a coherent response. Don't paste raw outputs — summarize and integrate.

---

## Cost Awareness

Each sub-agent has its own context window = its own token cost.

| Decision | Impact |
|----------|--------|
| 3 workers vs 10 workers | 3× vs 10× base prompt cost |
| 500-word vs 2000-word task prompt | Direct multiplier per worker |
| Cheap model for mechanical work | Significant savings |

Use the cheapest model that handles the task. Save expensive models for judgment-heavy work.

---

## Pre-Built Compositions

### Deal Review (Expert Panel)
Spawn legal, sales, finance experts in parallel → merge into unified brief with G/Y/R risk per domain.

### Product Launch (Pipeline)
PM spec → Marketing campaign → Sales battlecard → Support KB → Launch project tracker.

### Incident Response (Supervisor)
Security assessment → containment → trace analysis → legal obligations → customer comms → incident project.

### QBR Preparation (Fan-Out)
Finance, sales, product, data, marketing reports in parallel → executive package.

### Customer Research (Cascade)
Memory recall → email search → ticket search → synthesize with confidence scores → draft response.

### Skill Factory (Pipeline)
Scout → acquire/create → security scan → install → monitor → auto-repair on error.

---

## Integration

- **agent-guardrails**: Sub-agents inherit T2-max. Design workflows so T3+ actions return to the parent for execution with guardrails.
- **agent-memory**: Sub-agents can't access the memory store. Recall relevant context yourself and include it in task prompts.
- **Heartbeat**: Use `orchestrator.py status` in heartbeats to check on long-running workflows.

---

## Tools Reference

```
orchestrator.py create --type X --subtasks [...]     Register workflow
orchestrator.py update --id X --task-id Y --status Z Track progress
orchestrator.py status --id X                        View progress
orchestrator.py aggregate --id X                     Combine results
orchestrator.py list [--active]                      Overview
orchestrator.py cleanup [--days 7]                   Prune old data
task_templates.py list                               Available templates
task_templates.py preview <name>                     Rendered prompt

All: python3 skills/agent-orchestration/scripts/<script>
```

---

## Quick Reference Card

```
PATTERNS: Fan-Out (parallel) | Pipeline (sequential) | Supervisor (adaptive) | Expert Panel (consensus) | Map-Reduce (data)
DECIDE:   <5min→inline | independent→Fan-Out | sequential→Pipeline | opinions→Panel | data→Map-Reduce | complex→Supervisor
CONTEXT:  Minimum viable. Role + Task + Constraints + Output Format + <result> tags. Cut everything else.
SPAWN:    sessions_spawn(task=..., label="wf_<id>_<task>_<desc>", runTimeoutSeconds=N)
TRACK:    Always use ledger. Update on spawn, complete, fail.
RETRY:    Max 2 per task. Include error in retry prompt. 3+ failures → stop and ask user.
WORKERS:  3-6 parallel max. Each 5-15 min. T2-max (no T3+ actions).
COST:     Cheapest model that works. Prompt words × workers = total cost.
RECOVER:  Partial results > no results. Report honestly what failed.
```

---

## Workflow Engine Integration

The orchestrator now has a **workflow engine** (`lib/workflow_engine.py`) that bridges shared state, skill contracts, and this skill's coordination patterns into a unified system.

### Creating a Workflow

Instead of manually tracking subtasks in the orchestrator ledger, use the workflow engine to auto-create WorkItems with proper dependencies:

```python
from lib.workflow_engine import WorkflowEngine, load_workflow, list_workflows

engine = WorkflowEngine()

# Create a pipeline — each stage gets a WorkItem with dependency on the previous
wf = engine.create_pipeline(
    name="implement-auth-refresh",
    project="mpmp",
    stages=[
        {"capability": "implement", "goal": "Build refresh token endpoint"},
        {"capability": "testing", "goal": "Write integration tests"},
        {"capability": "deploy", "goal": "Deploy to staging"},
        {"capability": "verification", "goal": "Verify deployment health"},
    ],
)
print(wf.summary())
# Shows each stage with auto-resolved skill from contracts:
#   ⏳ 0. [implement] Build refresh token endpoint → python-backend
#   ⏳ 1. [testing] Write integration tests → python-backend
#   ⏳ 2. [deploy] Deploy to staging → devops
#   ⏳ 3. [verification] Verify deployment health → sanity-check
```

### Advancing Stages

```python
# Start the first unblocked stage
stage = engine.advance(wf)
# → Starts stage 0, sets WorkItem to in_progress

# When a stage completes (sub-agent reports back, or inline work finishes):
engine.complete_stage(wf, stage_index=0)

# Get post-hook tasks to spawn (sanity-check, reflect, skill-lifecycle)
hooks = engine.get_post_hook_tasks(wf, stage_index=0)
for hook in hooks:
    sessions_spawn(task=hook["description"], label=f"hook_{hook['skill']}")

engine.mark_post_hooks_run(wf, stage_index=0)

# Advance to next stage
next_stage = engine.advance(wf)
```

### Skill Contracts for Routing

Skills declare their capabilities in `config/skill_contracts/<name>.json`. The engine uses these to auto-route:

```python
from lib.skill_contract import find_skills_for, load_contract, build_pipeline

# Find skills that can deploy
deployers = find_skills_for(capability="deploy")
# → [devops]

# Find skills that can verify
verifiers = find_skills_for(capability="verification")
# → [sanity-check]

# Build a full pipeline from capability names
pipeline = build_pipeline(["implement", "deploy", "verification"])
# → [python-backend, devops, sanity-check]

# Read a specific contract
contract = load_contract("python-backend")
print(contract.inputs)       # What it needs
print(contract.outputs)      # What it produces
print(contract.downstream)   # Where work flows next
```

### Shared State for Tracking

Every stage creates a WorkItem (`lib/shared_state.py`) that the assigned skill updates during execution:

```python
from lib.shared_state import load_item, list_items

# Check progress on a stage
wi = load_item("wf-implement-auth-refresh-stage-0")
print(wi.status)      # in_progress / done / failed
print(wi.artifacts)   # Files produced
print(wi.tests)       # Test results
print(wi.findings)    # Lessons learned

# List all active work
for wi in list_items(status="in_progress"):
    print(wi.summary())
```

### Post-Stage Hooks (Evolution Loop)

After each stage completes, the engine generates post-hook tasks:

1. **sanity-check** — Runs OUTPUT gate on the completed WorkItem's artifacts and tests. Blocks promotion if issues found.
2. **reflect** — If the WorkItem has findings, encodes them into SOUL.md/TOOLS.md so the lesson persists.
3. **skill-lifecycle** — Monitors the executing skill's health metrics. Opens repair tickets if quality drifts.

This is the **evolution loop**: every piece of work feeds back into the agent's knowledge and the skill system's health.

### CLI Inspection

```bash
# List all work items
bin/shared-state list
bin/shared-state list --status in_progress

# Show full state of a work item
bin/shared-state show wf-implement-auth-refresh-stage-0

# View recent events
bin/shared-state tail wf-implement-auth-refresh-stage-0 --limit 5

# Dependency graph
bin/shared-state graph

# Check hook events
bin/shared-state hooks completed --since 2026-02-14

# Aggregate stats
bin/shared-state stats
```

### Decision: Workflow Engine vs Manual Orchestration

| Scenario | Use |
|----------|-----|
| Multi-stage software task (implement → test → deploy) | **Workflow Engine** — auto-creates WorkItems, chains deps, generates hooks |
| One-off parallel batch (document 30 skills) | **Manual Fan-Out** — overhead of contracts not worth it for homogeneous tasks |
| Expert panel / consensus review | **Manual Expert Panel** — no linear dependency chain to model |
| Recurring known pipeline (PR review → merge → deploy) | **Workflow Engine** — define once, reuse |
| Ad-hoc exploration or research | **Inline** — no orchestration needed |
