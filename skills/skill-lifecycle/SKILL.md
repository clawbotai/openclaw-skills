---
name: skill-lifecycle
version: 1.0.0
description: "Unified skill lifecycle management — Research→Build→Reflect evolutionary loop with AIOps runtime monitoring, error classification, circuit breakers, and self-healing repair tickets. Use for autonomous skill development, quality assurance, and operational observability."
triggers:
  - skill development
  - build skill
  - skill quality
  - skill monitoring
  - skill errors
  - self-healing
  - evolutionary loop
  - research and build
---

# Skill Lifecycle Management

Unified system for autonomous skill development and operational monitoring. Two integrated subsystems:

1. **Evolutionary Loop** — Research→Build→Reflect helix for creating and improving skills
2. **Runtime Monitor** — AIOps observability layer that intercepts failures, classifies errors, and generates repair tickets

Together they form a self-healing cycle: the monitor detects problems, the evolutionary loop fixes them.

---

# Part 1: Evolutionary Loop


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

---

# Part 2: Runtime Monitor


# Skill Runtime Monitor 🔭

The observability layer between the AI agent and its skills. Every skill execution passes through this monitor. When things break, we don't just log a stack trace — we diagnose, deduplicate, quarantine repeat offenders, and generate repair tickets that the Evolutionary Loop can act on.

**Philosophy:** An error log that says `KeyError: 'data'` is useless. An error log that says `KeyError: 'data'` when `input_args={'url': 'example.com', 'parse_mode': 'fast'}`, with 47 occurrences, a suggested fix, and the source code attached — that's actionable intelligence.

---

## Architecture

Four modules, one system:

```
┌─────────────────────────────────────────────────────────┐
│                  SKILL EXECUTION                        │
│  Agent calls a skill (Python function or subprocess)    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  MODULE 1: MONITOR (Interceptor)                        │
│  • @monitor_skill decorator wraps execution             │
│  • Captures: args, environment, traceback on failure    │
│  • Circuit breaker: quarantine after N failures         │
│  • Classifies: transient vs deterministic               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  MODULE 2: AGGREGATOR (Ledger)                          │
│  • Persistent JSON at memory/skill-errors.json          │
│  • Fingerprint deduplication (same error = count++)     │
│  • Rolling window: 7 days / 100 entries per skill       │
│  • Thread-safe I/O (threading.Lock)                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  MODULE 3: ANALYST (Surfacing)                          │
│  • Cross-skill reliability reports                      │
│  • Velocity alerts (error rate spikes)                  │
│  • Argument correlation (which inputs cause failures)   │
│  • Top offenders ranking                                │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  MODULE 4: BRIDGE (Feed Reflection)                     │
│  • Generates LLM-optimized RepairTickets                │
│  • Locates and attaches failing skill source code       │
│  • Suggests fix approach based on error patterns        │
│  • Exports directly to Evolutionary Loop Phase 3        │
└─────────────────────────────────────────────────────────┘
```

---

## How to Use

### For the Agent (Primary Usage)

When executing skills, wrap them through the monitor. The agent should:

1. **Before calling any skill:** Check if it's quarantined
2. **On failure:** The monitor handles logging automatically
3. **Periodically:** Generate a reliability report to surface issues
4. **When issues accumulate:** Export repair tickets for the Evolutionary Loop

### CLI Commands

Run from the `scripts/` directory:

```bash
# View overall reliability report
python3 scripts/monitor.py status

# View pending repair tickets (LLM-readable)
python3 scripts/monitor.py tickets

# Health details for a specific skill
python3 scripts/monitor.py health <skill_name>

# Clean up old error entries
python3 scripts/monitor.py prune

# Export repair tickets to file
python3 scripts/monitor.py export --output /path/to/tickets.md

# Reset a quarantined skill's circuit breaker
python3 scripts/monitor.py reset <skill_name>
```

Set `OPENCLAW_WORKSPACE` environment variable to point to the workspace root. Defaults to current directory.

### Python API

```python
from scripts.monitor import SkillMonitor, monitor_skill
from scripts.schemas import MonitorConfig

# Initialize with defaults
monitor = SkillMonitor(workspace="/path/to/workspace")

# Or customize thresholds
config = MonitorConfig(
    fail_threshold=5,       # Failures before circuit opens
    window_seconds=300,     # 5-minute failure window
    cooldown_seconds=600,   # 10-minute quarantine
    auto_ticket_threshold=3 # Min occurrences for repair ticket
)
monitor = SkillMonitor(config=config, workspace="/path/to/workspace")

# Decorator pattern
@monitor_skill(monitor)
def my_skill(arg1, arg2):
    ...

# Runtime wrapping
result = monitor.execute("skill-name", some_function, (arg1,), {"key": val})

# Subprocess skills (shell scripts, external tools)
result = monitor.execute_subprocess("skill-name", "bash scripts/run.sh", timeout=120)

# Analytics
report = monitor.generate_reliability_report()
print(report.to_summary())

# Argument correlation
correlations = monitor.get_argument_correlation("skill-name")

# Export for Evolutionary Loop
tickets = monitor.export_for_evolution()
payload = monitor.export_evolution_payload()  # Full LLM-readable string
```

---

## Error Classification

The monitor classifies every error into two categories. This distinction is critical — it determines whether the Evolutionary Loop should attempt a code fix or just wait for the environment to recover.

### Transient Errors (Don't Fix Code)

Environmental failures that usually resolve on retry:
- Network: timeouts, DNS failures, connection resets
- HTTP: 429 (rate limit), 502/503/504 (server issues)
- Resource: out of memory, disk full, quota exceeded
- Process: SIGTERM, SIGKILL (external termination)

**Agent action:** Retry later. Don't generate a repair ticket.

### Deterministic Errors (Fix Code)

Logic failures that will ALWAYS fail for the same input:
- Type/Value: TypeError, KeyError, IndexError, ValueError
- Validation: Pydantic errors, schema mismatches
- Import: missing modules, broken dependencies
- Logic: assertion failures, permission errors

**Agent action:** Generate a repair ticket. Feed to Evolutionary Loop.

### Classification Strategy

The classifier scores both categories from the error text and biases toward deterministic. Rationale: a false negative (missing a real bug) costs more than a false positive (investigating a transient). If in doubt, it's deterministic.

---

## Circuit Breaker

Borrowed from microservices resilience patterns (Nygard, "Release It!"), adapted for AI agents where every failed call wastes tokens.

```
CLOSED ──(N failures in T seconds)──→ OPEN
   ↑                                     │
   │                              (cooldown expires)
   │                                     │
   └──(probe succeeds)──── HALF_OPEN ←───┘
                               │
                        (probe fails)
                               │
                               └──→ OPEN
```

**Defaults:**
- `fail_threshold`: 5 failures
- `window_seconds`: 300 (5 minutes)
- `cooldown_seconds`: 600 (10 minutes)

When a skill is quarantined (OPEN), all calls are rejected immediately with a `RuntimeError` explaining the quarantine status. This prevents the agent from burning tokens on known-broken tools.

---

## Error Fingerprinting

The same logical error produces the same fingerprint, even across runs:

1. Take: `skill_name + error_type + error_message + traceback`
2. Normalize: strip line numbers, memory addresses, timestamps
3. Hash: SHA-256, truncated to 16 chars

Result: 50 identical `KeyError: 'data'` failures = 1 entry with `count: 50`. The ledger stays compact and readable.

---

## The Ledger (`memory/skill-errors.json`)

Persistent, indexed by skill name:

```json
{
  "parse_api_response": {
    "total_calls": 150,
    "total_failures": 12,
    "total_successes": 138,
    "transient_errors": 2,
    "deterministic_errors": 10,
    "circuit": {"state": "closed", "failure_count": 0},
    "errors": [
      {
        "fingerprint": "7dcebc9afaa568d8",
        "error_class": "deterministic",
        "error_type": "KeyError",
        "error_message": "'data'",
        "input_args": {"response": "{dict, keys=['status']}"},
        "count": 10,
        "first_seen": "2026-02-10T...",
        "last_seen": "2026-02-11T..."
      }
    ]
  }
}
```

**Self-maintenance:**
- Entries older than 7 days are pruned automatically
- Max 100 error entries per skill (oldest removed first)
- Corrupted ledger is backed up and a fresh one starts

---

## Repair Tickets (Bridge to Evolutionary Loop)

The monitor's primary output for self-healing. A RepairTicket contains everything an LLM needs to fix a broken skill:

| Field | Purpose |
|-------|---------|
| `skill_name` | Which skill is broken |
| `skill_source` | Actual source code (auto-located) |
| `error_type` + `error_message` | What went wrong |
| `traceback` | Full stack trace |
| `failing_input` | The exact args that trigger the failure |
| `occurrence_count` | How many times (urgency signal) |
| `failure_rate` | Skill-wide health metric |
| `suggested_fix_approach` | Pattern-matched suggestion |

### Priority Levels

| Priority | Trigger |
|----------|---------|
| CRITICAL | Skill quarantined (circuit breaker OPEN) |
| HIGH | >50% failure rate OR 10+ occurrences |
| MEDIUM | 5+ occurrences |
| LOW | Below thresholds but deterministic |

### Feeding into the Evolutionary Loop

The monitor exports repair tickets in a format designed for `skill-evolutionary-loop` Phase 3:

```python
# Generate the payload
payload = monitor.export_evolution_payload()

# Write it where the Evolutionary Loop can find it
Path("memory/repair-tickets.md").write_text(payload)
```

The Evolutionary Loop's Phase 3 (Reflection) reads this file and creates concrete fixes for each ticket. See the integration section below.

---

## Integration with Evolutionary Loop

The `skill-evolutionary-loop` skill reads repair tickets from this monitor as an additional input to its Phase 3 reflection process.

### Data Flow

```
skill-runtime-monitor                    skill-evolutionary-loop
─────────────────────                    ───────────────────────
                                         Phase 1: Research
                                              │
                                         Phase 2: Build
                                              │
Ledger → Analyst → RepairTickets ──────→ Phase 3: Reflect
                                              │
                                         Lessons → SOUL.md
                                         Fixes  → Skill code
```

### How to Trigger

When the agent detects accumulated errors (via reliability report or heartbeat check):

1. Run `monitor.export_evolution_payload()` to generate tickets
2. Write the payload to `memory/repair-tickets.md`
3. Invoke the Evolutionary Loop with the repair context:

```
"Start evolutionary loop Phase 3 (Reflection).
Read memory/repair-tickets.md for repair tickets from the runtime monitor.
For each CRITICAL/HIGH ticket:
  1. Locate the failing skill source
  2. Analyze the error + failing input
  3. Generate a fix
  4. Validate with backpressure gates
  5. Record lessons in memory/lessons.md"
```

---

## Reliability Report

The `generate_reliability_report()` function produces a cross-skill overview:

```
# Skill Reliability Report — 2026-02-11T22:43:01

**Skills Monitored:** 15
**Healthy:** 12 | **Degraded:** 2 | **Quarantined:** 1
**Pending Repair Tickets:** 3

## ⚠️ Velocity Alerts
- parse_api_response: error rate increased 200% (5 → 15 in last 24h)
- fetch-weather: NEW errors detected — 8 in last 24h (none previously)

## Top Offenders
- **parse_api_response**: 100.0% failure rate (15 deterministic errors)
- **fetch-weather**: 75.0% failure rate (6 deterministic errors)
```

### Argument Correlation

When the analyst detects that specific input patterns correlate with failures:

```
parse_api_response:
  arg 'response' = '{dict, keys=['status']}' — 47x (94% of failures)
  → Failures cluster when 'data' key is missing from response dict
```

This tells the Evolutionary Loop exactly what edge case to handle.

---

## File Structure

```
skill-runtime-monitor/
├── SKILL.md                    # This file — agent instructions
├── _meta.json                  # ClawHub-compatible metadata
└── scripts/
    ├── schemas.py              # Pydantic models (ErrorLog, SkillHealth,
    │                           #   RepairTicket, ReliabilityReport, MonitorConfig)
    ├── monitor.py              # Core engine (interceptor, aggregator,
    │                           #   analyst, bridge) + CLI
    └── usage_example.py        # Full demo: broken skill → quarantine →
                                #   report → repair ticket export
```

### Runtime Files (created automatically)

```
workspace/
└── memory/
    ├── skill-errors.json       # Persistent error ledger
    └── repair-tickets.md       # Export for Evolutionary Loop (on demand)
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fail_threshold` | 5 | Failures before circuit opens |
| `window_seconds` | 300 | Time window for counting failures |
| `cooldown_seconds` | 600 | Quarantine duration before probe |
| `max_errors_per_skill` | 100 | Max deduplicated entries per skill |
| `retention_days` | 7 | Auto-prune errors older than this |
| `ledger_path` | `memory/skill-errors.json` | Where to persist the ledger |
| `auto_ticket_threshold` | 3 | Min occurrences to generate a repair ticket |
| `quarantine_ticket` | true | Auto-generate CRITICAL ticket on quarantine |

---

## Design Principles

1. **Bias toward deterministic.** When unsure if an error is transient or deterministic, classify it as deterministic. False negatives (missing real bugs) are more expensive than false positives (investigating a transient).

2. **Fingerprint, don't flood.** The same error 100 times = 1 entry with count 100. The ledger stays small enough for an LLM to read entirely.

3. **Circuit break early.** An AI agent paying per token should not repeatedly call a broken tool. Quarantine fast, probe cautiously.

4. **Context is everything.** An error without its triggering input is useless for reproduction. Always capture arguments.

5. **Thread safety is non-negotiable.** Agents may invoke multiple skills concurrently. All ledger I/O is lock-protected.

6. **Self-maintaining.** Rolling windows and max counts prevent unbounded growth. Corrupted ledger auto-recovers.
