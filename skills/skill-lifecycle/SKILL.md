---
name: skill-lifecycle
description: Unified skill lifecycle management combining the Research→Build→Reflect evolutionary loop with AIOps runtime monitoring, error classification, circuit breakers, and self-healing repair tickets.
---

# Skill Lifecycle

Skills are living systems, not static files. They drift from requirements, they break on new inputs, and they accumulate silent failure modes. This skill closes the loop between development and operations: the Evolutionary Loop builds and learns, the Runtime Monitor observes and escalates. Together they create a closed feedback cycle — monitor detects an error → classifies it → generates a repair ticket → Evolutionary Loop fixes it → monitor verifies the fix.

Two halves, one purpose:

- **Part 1: Evolutionary Loop** — Research → Build → Reflect, enforced by backpressure gates and progress logs.
- **Part 2: Runtime Monitor** — AIOps-grade observability with error classification, circuit breakers, and repair tickets ready for Phase 3 reflection.

---

## How the Loop Closes

```
Runtime Monitor                          Evolutionary Loop
───────────────                          ─────────────────
Skill invocation → monitor intercepts
    │
    ├── Failure? → classify (transient vs deterministic)
    │
    ├── Deterministic + threshold → repair ticket
    │
    ├── Ticket stored in memory/repair-tickets.md
    │
    └── Circuit breaker trips if failures persist
                                     │
                                     ▼
                            Phase 1: Research (if needed)
                                     │
                                     ▼
                            Phase 2: Build (gated iterations)
                                     │
                                     ▼
                            Phase 3: Reflect (process tickets,
                            update SOUL/memory, confirm fix)
                                     │
                                     ▼
                              Monitor observes success
```

The monitor prevents blind repetition of broken skills. The Evolutionary Loop provides the disciplined mechanism to fix them. Lessons from Phase 3 update SOUL.md and memory files so regressions are less likely.

---

# PART 1: EVOLUTIONARY LOOP

Philosophy: **Research before you code. Gate everything. Reflect so you never repeat the same mistake.**

Every task moves through three phases:

1. **Phase 1 — Research**: Understand the problem and produce SPECIFICATION.md.
2. **Phase 2 — Build**: Iterative implementation with strict gates (tests/lint/typecheck/build) and PROGRESS.md logging.
3. **Phase 3 — Reflect**: Compare results to the specification, process repair tickets, encode lessons permanently.

The helix can spiral backwards — reflection might send you back to research if the spec was wrong. That feedback is a feature, not a failure.

---

## When to Research vs When to Just Build

| Situation | Action |
|-----------|--------|
| Familiar domain, clear request, no external dependencies | **Skip full research.** Write a brief SPECIFICATION.md from existing knowledge, proceed to Phase 2. |
| New library/API, unknown domain, regulation/security implications | **Full research cycle.** Exhaustive SPECIFICATION.md with citations. |
| Conflicting or ambiguous requirements | **Targeted research.** Focus on ambiguous areas. |
| User explicitly requests research or high rigor | **Full research.** Confirm via summary before building. |
| Bugfix with known input/output | **Minimal research.** Review existing code, reproduce bug, update SPECIFICATION.md with defect description. |

Decision tree:
```
Is the domain new or regulated?
  YES → Full research (Phase 1)
  NO → Are requirements ambiguous?
         YES → Targeted research
         NO  → Can you restate the problem in one paragraph?
                 YES → Minimal research, proceed to build
                 NO  → Clarify with user or research
```

---

## Phase 1: Research (The Eyes)

Goal: Produce SPECIFICATION.md with no unsourced assertions. Each claim must cite a source or be labeled as an assumption.

### Workflow

1. **Decompose into sub-questions.** 3–5 questions covering architecture, constraints, risks.
2. **Search broadly.** Use DuckDuckGo queries with synonyms and date filters ("2025"/"2026").
3. **Deep-read authoritative sources.** Official docs > academic > reputable blogs > forums.
4. **Cross-reference.** Resolve conflicts, flag uncertain areas in "Open Questions".
5. **Write SPECIFICATION.md.** Template:

```
# SPECIFICATION.md
Generated: 2026-02-13 | Sources: 12 | Confidence: Medium

## Objective
One paragraph summary of what will be built.

## Requirements
### Functional
- Requirement — Source: [link]

### Non-Functional
- Performance constraint — Source: [link]

## Technical Decisions
### Decision: Use library X
- Rationale
- Trade-offs
- Sources

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Open Questions
- Items needing clarification or future research

## Sources
1. [Title](url) — summary
```

### Spec Discipline

- No code in SPECIFICATION.md.
- No "we'll figure it out later" statements. If unknown, mark as Open Question.
- For bugfixes, capture reproduction steps, failing input, expected vs actual behavior.

---

## Phase 2: Build (The Body)

Goal: Implement the specification through iterative loops with enforced quality gates. Every iteration is logged in PROGRESS.md.

### Project Files

```
project-root/
├── SPECIFICATION.md           # Immutable requirements
├── IMPLEMENTATION_PLAN.md     # Living task list
├── PROGRESS.md                # Iteration log
├── src/                       # Code
└── tests/                     # Tests
```

### Implementation Plan

Derived from the specification.

```
# IMPLEMENTATION_PLAN.md
## Tasks (priority order)
- [ ] Task 1 — Acceptance criteria
- [ ] Task 2 — Acceptance criteria

## Backlog
- [ ] Nice-to-haves
```

### Iteration Cycle

```
Pick next task → Implement → Run gates → Success?
   │                   │           │
   │                   │           ├── Yes → Log PASS, commit, next task
   │                   │           └── No  → Diagnose, fix, retry (max 3)
   │                   │
   │             Gates: test → lint → typecheck → build
   │                   │
   └── Blocked? → Log BLOCKED with details, escalate to reflection
```

### Backpressure Gates

Configure per tech stack. Example (Python):
```yaml
gates:
  test: "python -m pytest tests/ -x --tb=short"
  lint: "ruff check src/"
  typecheck: "mypy src/ --ignore-missing-imports"
  build: "python -m compileall src/"
```

Rules:
- All gates must pass before marking a task complete.
- If a gate fails, fix the specific issue before touching other code.
- Max three retries per gate. After that, log BLOCKED and return to Phase 1 or escalate to Phase 3 reflection.

### Progress Logging (mandatory)

Append after every iteration:

```
## Iteration 5 — 2026-02-13T14:22Z
Task: Implement CSV export
Result: FAIL (typecheck)
Gates:
- Tests: PASS
- Lint: PASS
- Typecheck: FAIL (mypy: Incompatible return type)
- Build: SKIPPED (blocked earlier)
Retries: 2 (adjusted return type, added Optional handling)
Next: Fix type hints, retry typecheck
```

### Completion Criteria

- All tasks in IMPLEMENTATION_PLAN.md checked off.
- Final gate run passes.
- PROGRESS.md entry with `## Status: COMPLETE ✅`, list of changed files, testing instructions.

---

## Phase 3: Reflect (The Brain)

Goal: Compare outcomes to intent, process runtime repair tickets, encode lessons permanently, and close the loop with the monitor.

### Triggers

| Event | Reflection Type |
|-------|-----------------|
| Phase 2 completes | Standard reflection |
| Gate fails >3 times | Failure reflection |
| User correction | High-confidence reflection |
| Runtime monitor ticket | Monitor-driven reflection |
| Session ends | Boundary reflection |

### Process

1. **Gather evidence:** task request, SPECIFICATION.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, user feedback, `memory/repair-tickets.md` (if present).
2. **Identify signals:** high/medium/low confidence lessons. Monitor tickets are high-confidence — they happened in production.
3. **Classify lessons:** agent behavior → SOUL.md; technical pattern → `memory/lessons.md`; tool usage → TOOLS.md; skill improvement → this SKILL.md; domain knowledge → SPEC addendum.
4. **Propose changes:** For each lesson, define target file, diff, confidence.
5. **Apply:** High-confidence lessons (user corrections, monitor tickets) apply immediately. Medium-confidence require confirmation. Low-confidence log only.
6. **Log results:** Update `memory/lessons.md` with context and application status.

### Processing Repair Tickets

`memory/repair-tickets.md` contains monitor-generated tickets. For each:
1. Reproduce failure using provided input.
2. Create/adjust IMPLEMENTATION_PLAN task for the fix.
3. Run Phase 2 loop to implement and gate the fix.
4. Reflect on why the bug happened. Update SOUL/memory to prevent recurrence.
5. Delete or mark the ticket as resolved.

---

# PART 2: RUNTIME MONITOR

The monitor watches every skill invocation. It intercepts calls, classifies failures, prevents repeated failures through circuit breakers, and generates repair tickets with full context (inputs, tracebacks, occurrence counts).

Goal: Provide actionable diagnostics for the Evolutionary Loop and prevent token waste on known-broken skills.

---

## Architecture

```
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Skill Call    │→→ │ Monitor       │→→ │ Aggregator    │→→ │ Repair Bridge │
│ (function or  │   │ (decorator /  │   │ (ledger)      │   │ (tickets)     │
│ subprocess)   │   │ wrapper)      │   │               │   │               │
└──────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
                         │                       │                     │
                         │ circuit breaker       │ analytics           │ export to
                         │ classification        │ velocity alerts     │ Evolutionary Loop
```

### Key Concepts

- **Decorator/Wrapper:** `@monitor_skill` or `monitor.execute(...)` intercepts calls.
- **Ledger:** `memory/skill-errors.json` stores deduplicated error fingerprints with counts, timestamps, input args, classification (transient/deterministic).
- **Circuit Breaker:** Trips after `fail_threshold` within `window_seconds`, quarantine for `cooldown_seconds`.
- **Repair Tickets:** Generated when deterministic errors exceed thresholds or when a skill is quarantined. Saved to `memory/repair-tickets.md` for Phase 3.

### Error Classification

| Type | Examples | Action |
|------|----------|--------|
| **Transient** | Network timeouts, 5xx, rate limits, resource exhaustion | Log, retry later. No ticket. |
| **Deterministic** | TypeError, KeyError, validation failure, missing dependency | Generate repair ticket. |

Bias toward deterministic when uncertain — missing a real bug costs more than investigating a transient glitch.

### Circuit States

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

Defaults: `fail_threshold=5`, `window_seconds=300`, `cooldown_seconds=600`.

---

## CLI Usage

```bash
# Status + velocity alerts
python3 scripts/monitor.py status

# Health for specific skill
python3 scripts/monitor.py health <skill>

# View pending repair tickets
python3 scripts/monitor.py tickets

# Export tickets for Evolutionary Loop
python3 scripts/monitor.py export --output memory/repair-tickets.md

# Reset circuit breaker
python3 scripts/monitor.py reset <skill>

# Prune stale errors (>7 days)
python3 scripts/monitor.py prune
```

Environment: set `OPENCLAW_WORKSPACE` (defaults to current directory).

### Python API

```python
from scripts.monitor import SkillMonitor, monitor_skill

monitor = SkillMonitor(workspace=WORKSPACE)

@monitor_skill(monitor)
def run_skill(payload):
    ...

# or
result = monitor.execute("skill-name", callable, args, kwargs)
```

---

## Repair Tickets

Each ticket includes:
- Skill name
- Source snippet (auto-located)
- Error type, message, traceback
- Input args/environment
- Occurrence count and failure rate
- Suggested fix approach (pattern-based)
- Priority (CRITICAL/HIGH/MEDIUM/LOW)

Priority mapping:

| Priority | Trigger | Action |
|----------|---------|--------|
| CRITICAL | Circuit breaker open | Immediate Evolutionary Loop fix |
| HIGH | Failure rate >50% or 10+ occurrences | Next iteration |
| MEDIUM | ≥5 occurrences | Queue for batch fix |
| LOW | Below thresholds | Log; fix opportunistically |

`monitor.export_evolution_payload()` creates a Phase 3-ready Markdown payload. Write it to `memory/repair-tickets.md` before invoking reflection.

---

## Anti-Patterns

### The Infinite Research Loop

**Pattern:** Spending hours researching every edge case for a simple change. SPECIFICATION.md grows but nothing gets built.

**Reality:** Analysis without execution produces zero value.

**Fix:** Follow the decision framework. Once the spec answers the core questions, move to Phase 2. Capture open questions for later.

### The Build Without Spec

**Pattern:** Jumping straight into coding without a specification. Requirements live in your head.

**Reality:** Gates fail, scope drifts, user feedback contradicts assumptions. Rework multiplies.

**Fix:** Always produce SPECIFICATION.md, even if it's one page. Confirm with the user. No spec, no build.

### The Reflection Skip

**Pattern:** Finishing Phase 2, seeing green tests, declaring victory without reflection.

**Reality:** Lessons aren't captured, the same bugs recur, SOUL.md stays stale.

**Fix:** Phase 3 is mandatory. Reflection catches blind spots and processes repair tickets. It's how the agent improves.

### The Silent Failure

**Pattern:** Skills fail quietly because errors are swallowed or logging is absent. Monitor sees success because errors never reach it.

**Reality:** Users experience failures, but the system thinks everything is fine.

**Fix:** Never suppress exceptions without logging. Always surface errors to the monitor. Add guards for unexpected None/KeyError cases. Ensure monitor wraps every skill invocation.

---

## Quick Reference Card

```
DECIDE:    Research?
             - New domain / ambiguous → Full research
             - Familiar / clear → Minimal spec

PHASE 1:   SPECIFICATION.md with sources
             - Sub-questions → search → cross-reference
             - Decisions + acceptance criteria + open questions

PHASE 2:   IMPLEMENTATION_PLAN.md → gated iterations
             - Gates: test → lint → typecheck → build
             - PROGRESS.md entry after every iteration
             - Max 3 retries per gate → else BLOCKED

PHASE 3:   Reflect + process repair tickets
             - Gather evidence
             - Classify lessons (SOUL, memory, tools, skill)
             - Apply high-confidence lessons immediately

MONITOR:   @monitor_skill wrapper or monitor.execute
             - Classify errors (transient vs deterministic)
             - Circuit breaker (5 failures / 5 min)
             - Repair tickets in memory/repair-tickets.md
             - CLI: status | health | tickets | export | reset | prune

LOOP:      Monitor detects → Ticket → Evolutionary Loop fixes →
           Monitor verifies → Lessons logged
```
