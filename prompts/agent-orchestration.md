# Prompt: Design the `agent-orchestration` Skill for an Autonomous AI Agent

## Context

You are designing a skill called `agent-orchestration` for **OpenClaw**, an open-source autonomous AI agent platform. OpenClaw agents run locally on macOS/Linux, communicate via messaging surfaces (Signal, Telegram, Discord, WhatsApp, webchat), and use Claude/GPT as their LLM backbone.

**OpenClaw's native multi-agent primitives:**
- `sessions_spawn(task, label, model, runTimeoutSeconds)` — Spawns an isolated sub-agent session that runs a task and announces the result back to the parent. Returns `childSessionKey` and `runId`.
- `sessions_send(sessionKey, message)` — Send a message into another active session.
- `sessions_list(kinds, activeMinutes, messageLimit)` — List active sessions with optional filters.
- `sessions_history(sessionKey, limit, includeTools)` — Fetch message history from another session.
- Sub-agents run in isolation: they have tool access (filesystem, exec, web) but NO access to the parent's conversation context unless explicitly provided in the task prompt.
- Sub-agents announce their results back to the parent session when complete. The parent receives a system message with the findings.
- Sub-agents can be given different models (`model` param) and thinking levels.
- There is NO shared memory between sessions — each session has its own context window.
- Sub-agents cannot spawn their own sub-agents (single depth only).
- Max concurrent sessions is limited by the platform (typically 5-10).

**Current state (what we're improving):** The agent spawns sub-agents ad-hoc with manually-written task prompts. There's no structured approach to: task decomposition for parallelism, result aggregation, failure handling, dependency chains, progress monitoring, or workload optimization. Every multi-agent workflow is improvised.

**Why this matters:** The arxiv survey on Agentic AI (2510.25445) distinguishes single-agent from multi-agent systems as fundamentally different architectural categories. Multi-agent orchestration is how complex tasks get decomposed into parallelizable units, how specialized agents handle their domains, and how results get synthesized. CrewAI, AutoGen, and LangGraph all exist because this problem is hard enough to need structure. OpenClaw has the primitives but no playbook.

## Platform Constraints

- **Runtime:** Python 3.9 on macOS ARM (Apple Silicon)
- **Dependencies:** Minimal. Pydantic available. No external services.
- **Storage:** Local filesystem, SQLite acceptable for workflow state.
- **Integration model:** This skill teaches the agent HOW to orchestrate, providing patterns, templates, and a workflow manager. The agent still uses OpenClaw's native `sessions_spawn`, `sessions_send`, `sessions_list`, and `sessions_history` tools to actually execute.
- **Key limitation:** Sub-agents are fire-and-forget with announcement. The parent can check on them via `sessions_history` but can't interrupt or redirect mid-run. Design around this constraint.
- **File budget:** SKILL.md < 700 lines. Python scripts well-commented. Total < 45KB.
- **Typing:** `typing.Optional[X]` not `X | None` (Python 3.9 compat)

## What to Design

### 1. SKILL.md — The Orchestration Playbook

**Workflow Patterns (the agent should learn when to use each):**

**Pattern 1: Fan-Out / Fan-In (Parallel)**
- Use when: Multiple independent subtasks with no dependencies
- Example: "Document all 38 skills" → spawn 5-8 sub-agents, each handling a batch
- Implementation: Decompose → spawn all → monitor via sessions_list → collect results as announcements arrive → synthesize
- Key decisions: How many parallel agents? (Consider: task granularity, token cost, rate limits). Rule of thumb: 3-6 parallel agents, batch work so each runs 5-15 minutes.

**Pattern 2: Pipeline (Sequential)**
- Use when: Each step depends on the previous step's output
- Example: "Research topic → write outline → draft content → review → publish"
- Implementation: Spawn step 1 → wait for result → extract output → feed into step 2 task prompt → repeat
- Key decisions: What state passes between stages? Keep it concise — sub-agents don't share context.

**Pattern 3: Supervisor / Worker**
- Use when: Complex task needing ongoing coordination and judgment
- Example: "Build and deploy a web application"
- Implementation: Parent (supervisor) decomposes the task, spawns workers for specific pieces, reviews results, decides next steps, may re-assign failed tasks
- Key insight: The parent agent IS the supervisor. It doesn't spawn a supervisor — it IS one.

**Pattern 4: Expert Panel (Consensus)**
- Use when: Decision quality matters more than speed. Multiple perspectives needed.
- Example: "Review this architecture for security, performance, and maintainability"
- Implementation: Spawn 3 specialist sub-agents with different system contexts (security expert, performance expert, architect) → collect all opinions → synthesize consensus
- Key decisions: How to handle disagreements? Weight by domain relevance.

**Pattern 5: Map-Reduce**
- Use when: Large dataset/corpus needs processing then aggregation
- Example: "Analyze all 38 skills and produce a unified scorecard"
- Implementation: Map phase (spawn agents, each processes a subset) → Reduce phase (parent aggregates all results into final output)

**Task Decomposition Framework:**
Before spawning any sub-agent, the orchestrator should answer:
1. **Can this be parallelized?** Are subtasks independent?
2. **What's the minimum context each sub-agent needs?** (Don't dump the entire project — give focused, specific task prompts)
3. **What does "done" look like?** Define success criteria in the task prompt so the sub-agent knows when to stop.
4. **What if it fails?** Define fallback: retry? skip? escalate to user?
5. **What's the cost/benefit?** Each sub-agent costs tokens. Is spawning worth it vs. doing it inline?

**Task Prompt Engineering:**
Sub-agent task prompts should follow a structure:
```
## Context
[Minimal background — only what's needed for THIS subtask]

## Task
[Specific, unambiguous instruction]

## Constraints
[Time limits, file paths, don't-touch rules]

## Output Format
[Exactly what the sub-agent should produce — structured data preferred]

## When Done
[Specific finishing steps — commit, save to file, etc.]
```

**Result Aggregation:**
When sub-agents announce results back:
- Parse the announcement for structured data (look for JSON, markdown tables, status indicators)
- Handle partial failures gracefully (if 1 of 6 sub-agents fails, use the 5 good results)
- Synthesize into a coherent response for the user
- Don't just paste all sub-agent outputs together — summarize and integrate

**Failure Handling:**
- **Timeout:** If a sub-agent doesn't complete within `runTimeoutSeconds`, it's killed. The parent should have a plan for this.
- **Error in results:** Sub-agent announces an error. Parent can: retry with modified prompt, skip that subtask, or escalate to user.
- **Retry policy:** Max 2 retries per subtask. On retry, include the error context in the new task prompt so the sub-agent doesn't repeat the mistake.
- **Circuit breaker:** If 3+ sub-agents fail on the same workflow, stop spawning and ask the user what's wrong.

**Progress Monitoring:**
- After spawning, periodically check `sessions_list` to see which sub-agents are still running
- For long workflows (>10 min), give the user a progress update
- Use labels effectively — label sub-agents with descriptive names so `sessions_list` output is meaningful

**Cost Awareness:**
- Each sub-agent session has its own context window and token costs
- The task prompt itself consumes tokens in every sub-agent
- Prefer fewer, larger batches over many tiny sub-agents
- Consider model selection: use a cheaper/faster model for mechanical tasks (formatting, simple transforms), save expensive models for judgment calls

### 2. Python Scripts

**`scripts/orchestrator.py`** — Workflow state manager:
- `plan(task_description, pattern)` → Decomposes a task into subtasks using the specified pattern, returns a workflow plan as JSON
- `track(workflow_id, subtask_id, status, result)` → Update workflow state
- `status(workflow_id)` → Current workflow status: total subtasks, completed, failed, in-progress, elapsed time
- `aggregate(workflow_id)` → Collect all completed subtask results, return structured summary
- `history([--limit N])` → List past workflows with outcomes
- Workflow state stored in `memory/workflows.json`
- CLI interface for all operations
- All output as structured JSON

**`scripts/task_templates.py`** — Template library:
- Pre-built task prompt templates for common patterns:
  - `code_review(files, focus_areas)` → task prompt for a code review sub-agent
  - `documentation(target_path, style)` → task prompt for a documentation sub-agent
  - `research(topic, depth, output_format)` → task prompt for a research sub-agent
  - `testing(code_path, test_framework)` → task prompt for a testing sub-agent
  - `refactor(code_path, goals)` → task prompt for a refactoring sub-agent
- Each template follows the structured format above
- Templates are customizable — the agent can modify them for specific needs

### 3. Integration Patterns

**How the agent decides to orchestrate vs. do inline:**
- Task estimated to take >15 minutes? → Consider orchestration
- Task has naturally parallel components? → Fan-out
- Task requires multiple expertise domains? → Expert panel
- Task is simple and takes <5 minutes? → Just do it inline, don't over-engineer

**Orchestration in practice (example walkthrough):**
Show a complete example of the agent receiving a user request, deciding to use fan-out, decomposing the task, writing task prompts, spawning sub-agents, monitoring progress, handling a failure, aggregating results, and delivering the final response to the user.

**Anti-patterns to avoid:**
- Spawning a sub-agent for a 30-second task (overhead > benefit)
- Putting the entire project context in every sub-agent's task prompt (token waste)
- Not defining output format (getting unusable free-form text back)
- Spawning 10+ agents simultaneously (rate limits, resource contention)
- Recursive orchestration dreams (sub-agents can't spawn sub-agents, don't try to work around this)

## Research References
- Agentic AI survey (arxiv 2510.25445): Multi-Agent Systems as distinct architectural category
- CrewAI: Role-based multi-agent orchestration with delegation
- AutoGen: Conversational multi-agent with human-in-the-loop
- LangGraph: Stateful multi-agent workflows with cycles
- McKinsey agentic AI: "Logic, memory, orchestration, and interface functions decoupled for modularity"

## Output Format
Produce:
1. Complete `SKILL.md` (the agent-facing orchestration playbook)
2. Complete `scripts/orchestrator.py` with full implementation
3. Complete `scripts/task_templates.py` with template library
4. `_meta.json` for the skill
5. A brief `README.md` for humans

Design for a real autonomous agent that needs to make orchestration decisions dozens of times per day. The patterns should be internalized, not looked up every time. The workflow manager should be lightweight — it tracks state so the agent can pick up where it left off if the session resets, but it doesn't try to be a full workflow engine. The templates should save the agent 80% of the prompt-writing work for common tasks.
