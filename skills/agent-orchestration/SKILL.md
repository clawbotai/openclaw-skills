# agent-orchestration — Multi-Agent Workflow Playbook

## What This Is

A structured system for decomposing complex tasks into sub-agent workflows. You are the **Orchestrator** — you create plans, spawn workers, track progress, and aggregate results. This skill gives you the patterns, tools, and discipline to do it well.

**Core primitive:** `sessions_spawn(task=..., label=..., runTimeoutSeconds=...)`

**Core constraint:** Sub-agents share NO memory with you. Everything they need must be in the task prompt.

---

## The 5 Patterns

### 1. Fan-Out / Fan-In (Parallel)

**When:** Multiple independent subtasks with no dependencies.

```
You (Orchestrator)
  ├── spawn Worker A (batch 1)
  ├── spawn Worker B (batch 2)
  ├── spawn Worker C (batch 3)
  └── collect all results → synthesize
```

**Example:** "Document all 30 skills" → 5 workers, 6 skills each.
**Sweet spot:** 3–6 parallel workers. Each runs 5–15 min.

### 2. Pipeline (Sequential)

**When:** Each step depends on the previous step's output.

```
You → spawn Step 1 → get result → spawn Step 2(result) → get result → spawn Step 3(result) → done
```

**Example:** "Research → outline → draft → review → publish"
**Key:** Pass ONLY the needed output between stages. Keep it compact.

### 3. Supervisor / Worker

**When:** Complex task needing ongoing coordination and judgment calls.

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

**When:** Decision quality matters more than speed. Need multiple perspectives.

```
You → spawn Security Expert
    → spawn Performance Expert
    → spawn Architecture Expert
    → collect all opinions → synthesize consensus
```

**Example:** "Review this system design for production readiness"
**Key:** Use ConsensusCheckTemplate with different expert_role values.

### 5. Map-Reduce

**When:** Large dataset needs processing then aggregation.

```
Map:    You → spawn N workers (each processes a partition)
Reduce: You → collect all outputs → aggregate into final result
```

**Example:** "Analyze all skill scripts for comment quality"
**Key:** Partition data evenly. The reduce step is YOUR job (don't spawn for it).

---

## Decision Tree: Which Pattern?

```
Is the task a single unit of work?
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

Is it a large dataset that needs processing + aggregation?
  YES → Map-Reduce
  NO  ↓

Is it complex with ongoing judgment needed?
  YES → Supervisor
```

**Rule of thumb:** If a task takes <5 minutes, do it inline. If >15 minutes, consider orchestrating.

---

## Operational Guide: Step by Step

### Step 1: Decompose the Request

Break the user's request into discrete subtasks. Ask:
- Can these run in parallel?
- What's the minimum context each worker needs?
- What does "done" look like for each subtask?

### Step 2: Register the Plan

```bash
python3 skills/agent-orchestration/scripts/orchestrator.py create \
  --type fan_out \
  --subtasks '[
    {"id": "t1", "label": "Review auth module"},
    {"id": "t2", "label": "Review API module"},
    {"id": "t3", "label": "Review data module"}
  ]'
```

This returns a `workflow_id`. Save it.

### Step 3: Generate Task Prompts

Use task_templates.py to build structured prompts:

```python
# In your reasoning (or via CLI preview):
python3 skills/agent-orchestration/scripts/task_templates.py preview code_review --files "src/auth.py"
```

Or reference the templates programmatically in your tool calls. Each template produces a self-contained prompt with an **Output Interface** section.

### Step 4: Spawn Sub-Agents

For each subtask, call `sessions_spawn`:

```
sessions_spawn(
    task=<rendered template prompt>,
    label="wf_abc123_t1_auth_review",
    runTimeoutSeconds=600
)
```

**Labeling convention:** `wf_<workflow_id>_<task_id>_<description>`

Update the ledger:
```bash
python3 orchestrator.py update --id wf_abc123 --task-id t1 --status in_progress --session-key <key>
```

### Step 5: Monitor Progress

Periodically check:
```bash
python3 orchestrator.py status --id wf_abc123
```

Also use `sessions_list` to see which sub-agents are still running.

For long workflows (>10 min), give the user a progress update.

### Step 6: Collect Results

When a sub-agent announces its result, parse it:

The sub-agent wraps its answer in `<result>...</result>` tags (enforced by the template's Output Interface). Extract the content between tags.

Update the ledger:
```bash
python3 orchestrator.py update --id wf_abc123 --task-id t1 --status completed --result "<parsed output>"
```

### Step 7: Handle Failures

If a sub-agent fails or times out:
```bash
python3 orchestrator.py update --id wf_abc123 --task-id t1 --status failed --result "Timed out after 600s"
```

**Retry policy:**
- Max 2 retries per subtask
- On retry, include the error in the new task prompt
- If 3+ subtasks fail in the same workflow → stop and ask the user

### Step 8: Aggregate and Deliver

```bash
python3 orchestrator.py aggregate --id wf_abc123
```

This collects all completed results. Synthesize them into a coherent response for the user. Don't just paste outputs — summarize and integrate.

---

## Task Prompt Engineering

Every sub-agent prompt should follow this structure (enforced by templates):

```markdown
## Role
[Who the sub-agent is — one sentence]

## Task
[What to do — specific, unambiguous]

## Constraints
[Boundaries — time, scope, don't-touch rules]

## Expected Output Format
[Exact format — JSON schema preferred]

## Output Interface
[<result>...</result> wrapper instructions]
```

**Critical rules:**
- Give MINIMUM context — don't dump the whole project
- Define "done" explicitly
- Specify output format so you can parse it
- Include `<result>` tags so extraction is reliable

---

## Anti-Patterns

❌ **Spawning for trivial tasks** — If it takes <5 min, just do it yourself. The overhead of spawning + parsing + tracking costs more than the time saved.

❌ **Context dumping** — Don't paste your entire conversation or project state into every task prompt. Sub-agents have their own context windows. Give them only what they need.

❌ **No output format** — If you don't specify how the sub-agent should format its answer, you'll get free-form text you can't parse. Always use templates.

❌ **Over-parallelization** — More than 6 concurrent sub-agents causes resource contention and makes monitoring hard. Batch instead.

❌ **Recursive orchestration** — Sub-agents CANNOT spawn sub-agents (single depth). Don't try to work around this. If a subtask is too complex, break it down further in YOUR plan.

❌ **Fire and forget** — Always track with the ledger. If you don't update status, you can't recover after a session reset.

---

## Cost Awareness

Each sub-agent has its own context window = its own token cost.

| Decision | Token Impact |
|----------|-------------|
| 3 workers vs 10 workers | 3× vs 10× the base prompt cost |
| 500-word task prompt vs 2000-word | Direct multiplier |
| Using cheaper model for mechanical work | Significant savings |

**Guideline:** Use the cheapest model that can handle the task. Save expensive models for judgment-heavy work (code review, architecture decisions).

---

## Tools Reference

| Tool | Command | Purpose |
|------|---------|---------|
| Create plan | `orchestrator.py create --type X --subtasks [...]` | Register workflow |
| Update task | `orchestrator.py update --id X --task-id Y --status Z` | Track progress |
| Check status | `orchestrator.py status --id X` | View progress |
| Aggregate | `orchestrator.py aggregate --id X` | Combine results |
| List workflows | `orchestrator.py list [--active]` | Overview |
| Cleanup | `orchestrator.py cleanup [--days 7]` | Prune old data |
| List templates | `task_templates.py list` | See available templates |
| Preview template | `task_templates.py preview <name>` | See rendered prompt |

All paths: `python3 skills/agent-orchestration/scripts/<script>`
