---
name: skill-runtime-monitor
version: 1.0.0
description: "AIOps observability layer for skill execution. Intercepts failures, classifies errors (transient vs deterministic), maintains a deduplicated error ledger with circuit breaker logic, surfaces reliability analytics, and exports LLM-optimized repair tickets for the Evolutionary Loop."
triggers:
  - skill monitor
  - skill health
  - skill errors
  - reliability report
  - error report
  - quarantined skills
metadata:
  openclaw:
    emoji: "🔭"
    category: "observability"
---

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
