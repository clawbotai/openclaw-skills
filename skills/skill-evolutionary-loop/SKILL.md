---
name: skill-evolutionary-loop
version: 1.0.0
description: "Autonomous Research-Build-Reflect helix. Researches to understand, builds with backpressure gates, and reflects to permanently learn from mistakes."
triggers:
  - evo loop
  - evolutionary loop
  - research and build
  - ralph mode
  - deep build
  - autonomous build
metadata:
  openclaw:
    emoji: "🧬"
    category: "autonomous-development"
---

# Evolutionary Loop 🧬

A unified autonomous development skill that fuses three capabilities into a single helix:

- **The Eyes** — Deep research to understand before acting
- **The Body** — Iterative build loops with backpressure gates that reject bad work
- **The Brain** — Reflection that extracts lessons and permanently encodes them

Philosophy: **Research before you code. Gate everything. Correct once, never again.**

---

## The Helix Workflow

Every task passes through three phases in sequence. The helix can spiral — Phase 3 may reveal gaps that send you back to Phase 1. This is by design.

```
    ┌─────────────────────────┐
    │  PHASE 1: RESEARCH      │  ← The Eyes
    │  Understand the domain   │
    │  Output: SPECIFICATION.md│
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │  PHASE 2: BUILD         │  ← The Body
    │  Implement with gates    │
    │  Loop: Code→Test→Lint    │
    │  Output: Working code    │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │  PHASE 3: REFLECT       │  ← The Brain
    │  Compare result to spec  │
    │  Extract lessons learned  │
    │  Output: Updated SOUL.md │
    └────────────┬────────────┘
                 │
                 ╰──→ (spiral back if needed)
```

---

## Phase 1: Context Acquisition (The Research Layer)

**Goal:** Build a verified understanding of the domain before writing any code. Every claim in the specification must trace to a source.

### When to Research

Not every task needs research. Use this decision tree:

| Situation | Action |
|-----------|--------|
| Familiar domain, clear requirements | Skip to Phase 2, write a brief SPECIFICATION.md from knowledge |
| New library, API, or domain | Full research cycle |
| User says "research first" or "I want this done right" | Full research cycle |
| Conflicting or ambiguous requirements | Targeted research on the ambiguity |

### Research Workflow

**Step 1: Decompose into Sub-Questions**

Break the task into 3-5 research questions. Each must be answerable with evidence.

```markdown
## Task: "Build a WebSocket-based real-time dashboard"

Sub-questions:
1. What are the current best practices for WebSocket servers in [language]?
2. What authentication patterns work with persistent connections?
3. How do production systems handle reconnection and state recovery?
4. What are the performance characteristics at our expected scale?
5. Are there regulatory or security concerns for real-time data?
```

**Step 2: Multi-Source Search**

For each sub-question, search with 2-3 keyword variations:

```
Use web_search for each sub-question:
  - Primary query (direct question)
  - Alternative phrasing (different keywords)
  - Recent results (add "2025" or "2026" to query)
```

Strategy:
- Aim for 15-30 unique sources across all sub-questions
- Prioritize: official docs → academic → reputable tech → blogs → forums
- Use `web_search` for discovery, `web_fetch` for deep reads

**Step 3: Deep-Read Key Sources**

Select the 3-5 most authoritative sources and fetch full content:

```
Use web_fetch on each key URL.
Extract: facts, code patterns, configuration details, warnings.
```

**Step 4: Cross-Reference and Verify**

- If only one source makes a claim → flag as "unverified"
- If sources conflict → document both positions with citations
- If a gap exists → say so explicitly ("insufficient data found for X")

**Step 5: Write SPECIFICATION.md**

Output the research into a specification document in the project root:

```markdown
# SPECIFICATION.md
*Generated: [date] | Sources: [N] | Confidence: [High/Medium/Low]*

## Objective
[What we're building, in one paragraph]

## Requirements
### Functional
- [Requirement 1] — Source: [citation]
- [Requirement 2] — Source: [citation]

### Non-Functional
- [Performance target] — Source: [citation]
- [Security constraint] — Source: [citation]

## Technical Decisions
### Decision 1: [e.g., "Use library X over Y"]
- **Chosen:** X
- **Rationale:** [evidence-based reasoning]
- **Sources:** [links]
- **Trade-offs:** [what we give up]

## Acceptance Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

## Open Questions
- [Anything unresolved, flagged for Phase 2 discovery]

## Sources
1. [Title](url) — [one-line summary]
2. ...
```

**Rule: No unsourced assertions in SPECIFICATION.md.** If you can't cite it, flag it as an assumption.

---

## Phase 2: The Build Loop (The Execution Layer)

**Goal:** Implement the specification through iterative cycles with automatic quality gates that reject bad work.

### Setup

Before the first iteration, establish the project structure:

```
project-root/
├── SPECIFICATION.md           # From Phase 1 (read-only during build)
├── IMPLEMENTATION_PLAN.md     # Prioritized task list (living document)
├── PROGRESS.md                # Iteration-by-iteration log (append-only)
├── specs/                     # Detailed specs per topic (if needed)
├── src/                       # Application code
└── tests/                     # Test files
```

Create `IMPLEMENTATION_PLAN.md` from the specification:

```markdown
# Implementation Plan
*Derived from: SPECIFICATION.md*

## Tasks (Priority Order)
- [ ] Task 1: [description] — Criteria: [what "done" looks like]
- [ ] Task 2: [description] — Criteria: [what "done" looks like]
...

## Backlog
- [ ] Nice-to-have items
```

### The Iteration Cycle

Each iteration follows this exact sequence:

```
┌─ SELECT ──────────────────────────────┐
│ Pick highest-priority incomplete task  │
│ from IMPLEMENTATION_PLAN.md           │
└──────────────┬────────────────────────┘
               │
┌──────────────▼────────────────────────┐
│ IMPLEMENT                              │
│ Write code for ONE task only           │
│ Reference SPECIFICATION.md for context │
└──────────────┬────────────────────────┘
               │
┌──────────────▼────────────────────────┐
│ VALIDATE (Backpressure Gates)          │
│                                        │
│  Gate 1: Tests     → run test suite    │
│  Gate 2: Lint      → run linter        │
│  Gate 3: Typecheck → run type checker  │
│  Gate 4: Build     → verify it compiles│
│                                        │
│  ALL gates must pass to proceed.       │
└──────────────┬───────────┬────────────┘
               │           │
          PASS ▼      FAIL ▼
┌──────────────────┐ ┌─────────────────────┐
│ UPDATE & COMMIT  │ │ SELF-CORRECT        │
│ Mark task done   │ │ Read error output    │
│ Log to PROGRESS  │ │ Reference SPEC       │
│ Git commit       │ │ Fix and re-validate  │
│ Next iteration   │ │ Max 3 retries/gate   │
└──────────────────┘ └──────────┬──────────┘
                                │
                          Still failing?
                                │
                     ┌──────────▼──────────┐
                     │ ESCALATE            │
                     │ Log blocker         │
                     │ Jump to Phase 3     │
                     │ (Reflect on failure)│
                     └─────────────────────┘
```

### Backpressure Gate Configuration

Define gates in your project's context. Common configurations:

**Python:**
```yaml
gates:
  test: "python -m pytest tests/ -x --tb=short"
  lint: "ruff check src/"
  typecheck: "mypy src/ --ignore-missing-imports"
  build: "python -c 'import src'"
```

**Node/TypeScript:**
```yaml
gates:
  test: "npm run test"
  lint: "npm run lint"
  typecheck: "npx tsc --noEmit"
  build: "npm run build"
```

**Go:**
```yaml
gates:
  test: "go test ./..."
  lint: "golangci-lint run"
  typecheck: "go vet ./..."
  build: "go build ./..."
```

### Gate Failure Protocol

When a gate fails:

1. **Read the error output carefully.** Don't guess — parse the actual error.
2. **Reference SPECIFICATION.md** — does the error reveal a spec gap?
3. **Fix the specific failure.** Don't refactor adjacent code.
4. **Re-run the failing gate.** Only proceed when it passes.
5. **If 3 retries fail:** Stop. Log the blocker in PROGRESS.md. Trigger Phase 3 reflection.

### Progress Logging (Mandatory)

After **every** iteration, append to PROGRESS.md:

```markdown
## Iteration [N] — [ISO timestamp]

### Task
[What was attempted]

### Result
[PASS | FAIL | BLOCKED]

### Gate Results
- Tests: PASS/FAIL ([details if fail])
- Lint: PASS/FAIL
- Typecheck: PASS/FAIL
- Build: PASS/FAIL

### Retries
[Number of self-correction attempts, with what was tried]

### Files Changed
- `path/to/file` — [brief description]

### Next
[What the next iteration should tackle]
```

### Completion Signal

When all tasks in IMPLEMENTATION_PLAN.md are done:

1. Run all gates one final time
2. Write final PROGRESS.md entry with `## Status: COMPLETE ✅`
3. List all files created/modified
4. Provide testing instructions
5. Proceed to Phase 3

### Operational Constraints

| Parameter | Default | Override |
|-----------|---------|---------|
| Max iterations | 20 | Set in task prompt |
| Max retries per gate | 3 | Hardcoded |
| Iteration timeout | 10 min | Set in task prompt |
| Session timeout | 60 min | Set in task prompt |
| Max concurrent sessions | 1 per codebase | Enforced |

**Anti-patterns to avoid:**
- Spawning overlapping build sessions on the same codebase
- Silently stopping without a PROGRESS.md entry
- Assuming directory structure without verifying paths
- Refactoring unrelated code during a fix iteration

---

## Phase 3: The Reflection Guard (The Learning Layer)

**Goal:** Compare the outcome against the original intent, extract lessons, and permanently encode them so the agent improves over time.

### When Reflection Triggers

Reflection runs automatically when:

| Trigger | Action |
|---------|--------|
| Phase 2 completes successfully | Standard reflection |
| A gate fails >3 times | Failure reflection (deeper analysis) |
| The user corrects the agent | Correction reflection (highest priority) |
| Session ends or context compacts | Boundary reflection |
| Runtime monitor exports repair tickets | Monitor-driven reflection (automated) |

### The Reflection Process

**Step 1: Gather Evidence**

Collect the raw material for analysis:

- The original task request (what the user asked for)
- SPECIFICATION.md (what we planned)
- PROGRESS.md (what actually happened)
- Any user corrections or feedback during the session
- Gate failure logs (what went wrong mechanically)
- **`memory/repair-tickets.md`** (from skill-runtime-monitor, if it exists)

**Step 2: Signal Detection**

Scan the session for learning signals. Categorize by confidence:

| Confidence | Signal Type | Examples |
|------------|-------------|---------|
| **HIGH** | Explicit user correction | "No, do it this way", "Never use X", "Always Y" |
| **HIGH** | Repeated gate failure | Same test failing 3+ times |
| **MEDIUM** | User-approved pattern | "Perfect", "Exactly right", "That's what I wanted" |
| **MEDIUM** | Specification gap found during build | Assumption proved wrong |
| **LOW** | Implicit pattern | Something that worked but wasn't explicitly validated |

**Step 3: Classify Lessons**

Each lesson maps to a target:

| Lesson Category | Target File | Example |
|-----------------|-------------|---------|
| Agent behavior / preferences | `SOUL.md` | "User prefers functional style over OOP" |
| Technical pattern | `memory/lessons.md` | "Always check for null before accessing .data in API responses" |
| Tool usage | `TOOLS.md` | "Use web_fetch with maxChars=5000 for API docs" |
| Skill improvement | This SKILL.md | "Add Docker gate for containerized projects" |
| Domain knowledge | `SPECIFICATION.md` addendum | "This API rate-limits at 100 req/min" |
| New reusable pattern | New skill candidate | Non-trivial debugging breakthrough |

**Step 4: Generate Proposals**

Format each lesson as a concrete, applicable change:

```markdown
# Reflection Report — [Date]

## Session Summary
- **Task:** [original request]
- **Outcome:** [success / partial / blocked]
- **Iterations:** [N]
- **User Corrections:** [count]

## Lessons Detected

### Lesson 1: [Title]
- **Confidence:** HIGH
- **Source:** [user quote or error log]
- **Category:** [Agent behavior / Technical pattern / etc.]
- **Target:** [file path]
- **Proposed Change:**
  ```diff
  + [what to add or modify]
  ```

### Lesson 2: [Title]
...

## Quality Gates (all must pass before applying)
- [ ] Reusable: Will this help with future tasks?
- [ ] Non-trivial: Not something obvious from docs?
- [ ] Specific: Can describe exact trigger conditions?
- [ ] Verified: The lesson came from actual experience?
- [ ] No conflict: Doesn't contradict existing rules?
```

**Step 5: Apply Lessons**

For **HIGH confidence** lessons from explicit user corrections:
- Apply immediately (the user already told us what to do)
- Write to the target file
- Log the change in `memory/lessons.md`

For **MEDIUM confidence** lessons:
- Present to the user for approval before applying
- Format as a clear proposal with diff

For **LOW confidence** lessons:
- Log in `memory/lessons.md` for future reference
- Do not modify SOUL.md or SKILL.md without approval

### The Lessons Ledger

Maintain `memory/lessons.md` as a running log of everything learned:

```markdown
# Lessons Learned

## [Date] — [Task Name]

### What Happened
[Brief context]

### Lesson
[The specific learning]

### Applied To
[File path and section, or "logged only"]

### Confidence
[HIGH/MEDIUM/LOW]
```

This file is the agent's institutional memory. It survives across sessions.

### Updating SOUL.md

SOUL.md is the agent's permanent identity. Only write to it when:

1. The user explicitly corrects a behavior pattern
2. A preference is confirmed across multiple sessions
3. A fundamental operating principle is discovered

Format additions to SOUL.md as behavioral rules:

```markdown
## Learned Behaviors
- **[Date]:** [Rule in plain language]. *Source: [context]*
```

**Safety:** Never delete existing SOUL.md content. Only append. Never modify core identity sections without user approval.

---

## Integration: Skill Runtime Monitor → Phase 3

The `skill-runtime-monitor` skill continuously observes all skill executions and generates RepairTickets when deterministic errors accumulate. These tickets are a high-value input to Phase 3 reflection.

### Monitor-Driven Reflection

When `memory/repair-tickets.md` exists and contains tickets, Phase 3 should process them alongside normal reflection:

1. **Read** `memory/repair-tickets.md`
2. **For each ticket**, treat it as a HIGH confidence signal:
   - The error is verified (it happened in production, with real inputs)
   - The input that triggers it is captured
   - The source code is attached (if locatable)
   - A fix suggestion is provided
3. **Generate fixes** using the same Phase 2 build loop:
   - Create a branch or working copy
   - Apply the suggested fix
   - Run backpressure gates to validate
   - If gates pass → commit the fix
   - If gates fail → log as BLOCKED, escalate
4. **Record lessons** from each fix in `memory/lessons.md`
5. **Clear processed tickets** from `memory/repair-tickets.md`

### Ticket Priority Handling

| Priority | Evolutionary Loop Action |
|----------|--------------------------|
| CRITICAL | Immediate fix cycle — skill is quarantined and unusable |
| HIGH | Fix in next available iteration |
| MEDIUM | Queue for batch processing |
| LOW | Log only, fix if convenient |

### Generating Tickets from the Monitor

```python
# In your agent or heartbeat check:
from skills.skill_runtime_monitor.scripts.monitor import SkillMonitor

monitor = SkillMonitor(workspace="/path/to/workspace")
payload = monitor.export_evolution_payload()

if "No repair tickets pending" not in payload:
    Path("memory/repair-tickets.md").write_text(payload)
    # Trigger evolutionary loop Phase 3
```

### Closing the Loop

After the Evolutionary Loop fixes a skill:

1. The fix is committed and deployed
2. The runtime monitor observes the skill succeeding on previously-failing inputs
3. The error count stops incrementing
4. The circuit breaker resets (OPEN → HALF_OPEN → CLOSED)
5. The repair ticket is no longer generated

This creates a **self-healing cycle**: Monitor detects → Loop fixes → Monitor verifies.

---

## Sub-Agent Orchestration

For complex tasks, the evolutionary loop can spawn sub-agents for Phase 2 iterations:

```
Main Agent (Coordinator)
  │
  ├── Phase 1: Research (main agent — needs web_search/web_fetch)
  │
  ├── Phase 2: Build iterations (sub-agents)
  │     ├── Iteration 1: sessions_spawn(task="...", label="evo-iter-1")
  │     ├── Iteration 2: sessions_spawn(task="...", label="evo-iter-2")
  │     └── ...
  │
  └── Phase 3: Reflect (main agent — needs write access to SOUL.md)
```

When spawning build sub-agents:

```
sessions_spawn(
  task: "You are in Phase 2 of an Evolutionary Loop.

  READ THESE FILES FIRST:
  - SPECIFICATION.md (your requirements)
  - IMPLEMENTATION_PLAN.md (your task list)
  - PROGRESS.md (what's been done)

  YOUR TASK: Pick the next incomplete item from IMPLEMENTATION_PLAN.md.
  Implement it. Run all gates (test/lint/typecheck/build).
  If a gate fails, self-correct up to 3 times.
  Write your results to PROGRESS.md.
  Mark your task done in IMPLEMENTATION_PLAN.md.
  Commit your changes.

  GATES:
  [paste gate commands here]

  If you cannot complete the task after 3 retries, write BLOCKED status
  to PROGRESS.md with full error details and exit.",

  label: "evo-build-[N]"
)
```

**Coordination rules:**
- Only one build sub-agent active per codebase at a time
- Main agent checks PROGRESS.md between spawns
- If PROGRESS.md shows BLOCKED → trigger Phase 3 reflection
- If PROGRESS.md shows COMPLETE → proceed to Phase 3

---

## Quick Start

When the user invokes the evolutionary loop:

1. **Acknowledge** — "Starting evolutionary loop. Phase 1: researching the domain."
2. **Assess research need** — Does this task require research or is it straightforward?
3. **Execute Phase 1** — Research if needed, produce SPECIFICATION.md
4. **Present spec for approval** — "Here's what I plan to build. Approve to proceed?"
5. **Execute Phase 2** — Build loop with gates
6. **Execute Phase 3** — Reflect, extract lessons, update memory
7. **Report** — Final summary with what was built, what was learned, what changed

## Examples

```
"Use the evolutionary loop to build me a CLI tool that converts CSV to JSON"
"Evo loop: research and implement a rate limiter for our FastAPI app"
"Start an evolutionary build — I need a React component library with Storybook"
"Research-build-reflect: set up a CI/CD pipeline for this Python project"
```

## File Reference

| File | Purpose | Phase |
|------|---------|-------|
| `SPECIFICATION.md` | Research output, requirements | 1 |
| `IMPLEMENTATION_PLAN.md` | Prioritized task list | 2 |
| `PROGRESS.md` | Iteration-by-iteration build log | 2 |
| `memory/lessons.md` | Running log of all lessons learned | 3 |
| `SOUL.md` | Permanent agent identity & behaviors | 3 |
| `TOOLS.md` | Tool-specific notes & preferences | 3 |
| `memory/repair-tickets.md` | Repair tickets from skill-runtime-monitor | 3 |
| `memory/skill-errors.json` | Persistent error ledger (runtime monitor) | — |
