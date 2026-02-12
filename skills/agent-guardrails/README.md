# agent-guardrails

Self-sovereign safety layer for OpenClaw autonomous agents.

## What It Does

An advisory system the agent consults before taking risky actions:

- **4-tier action classification** (T1 Safe → T4 High Risk) with automatic promotion rules
- **Policy engine** — JSON-configurable rules, sensitive paths, rate limits, quiet hours
- **Sensitive data scanning** — AWS keys, OpenAI keys, GitHub tokens, PII, credit cards, prompt injections
- **Rate limiting** — 5 T3/min, 3 T4/hour (prevents runaway loops)
- **Audit trail** — Every action logged to SQLite with timestamps and decisions
- **Session cache** — Auto-approves repeated safe operations (reduces user fatigue)
- **File rollback** — Snapshots before modification, restore on demand, auto-prune

## Quick Start

```bash
# Classify an action
python3 skills/agent-guardrails/scripts/guardrails.py check --action send_email --target "bob@example.com"

# Scan for sensitive data
python3 skills/agent-guardrails/scripts/guardrails.py scan --text "key is sk-abc123def456"

# Log a decision
python3 skills/agent-guardrails/scripts/guardrails.py log --action git_push --tier T3 --decision APPROVED

# Snapshot before editing
python3 skills/agent-guardrails/scripts/snapshot.py save important_file.py

# Review audit trail
python3 skills/agent-guardrails/scripts/guardrails.py audit --limit 10
```

## Architecture

```
Agent wants to act
  → check (classify tier, rate limit, conditions)
  → scan (if external: detect secrets/PII/injections)
  → snapshot (if modifying files)
  → act (or ask user if T4)
  → log (record decision)
```

## No Dependencies

Pure Python 3.9+. SQLite for audit. No pip install needed.

See `SKILL.md` for the agent-facing behavioral contract.
