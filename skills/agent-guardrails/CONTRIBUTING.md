# Contributing to agent-guardrails

## Overview

This skill implements an advisory safety layer for autonomous AI agents. It classifies actions into risk tiers, scans for sensitive data, enforces rate limits, and maintains an audit trail — all backed by SQLite.

## File Structure

```
agent-guardrails/
├── SKILL.md              # Usage documentation and decision flowcharts
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # This file
├── policies.json         # Configurable policy rules (editable by the human)
├── _meta.json            # Skill metadata
├── scripts/
│   ├── __init__.py       # Package marker
│   ├── guardrails.py     # Core CLI: check, scan, log, audit, stats
│   └── snapshot.py       # File rollback: save, restore, list, prune
```

## Development Setup

**Requirements:** Python 3.10+ (stdlib only — no external dependencies).

```bash
# No virtual environment needed; uses only stdlib modules
python3 skills/agent-guardrails/scripts/guardrails.py --help
python3 skills/agent-guardrails/scripts/snapshot.py --help
```

## Running Tests

There is no formal test suite yet. To verify functionality manually:

```bash
# Check classification
python3 skills/agent-guardrails/scripts/guardrails.py check --action send_email --target "test@example.com"

# Scan for secrets
python3 skills/agent-guardrails/scripts/guardrails.py scan --text "key: sk-abc123xyz"

# Log and audit
python3 skills/agent-guardrails/scripts/guardrails.py log --action test --tier T2 --decision APPROVED
python3 skills/agent-guardrails/scripts/guardrails.py audit --limit 5

# Snapshot lifecycle
python3 skills/agent-guardrails/scripts/snapshot.py save README.md
python3 skills/agent-guardrails/scripts/snapshot.py list
python3 skills/agent-guardrails/scripts/snapshot.py prune --days 1
```

To add automated tests, create `tests/` with pytest and cover: tier classification, tier promotion logic, scan pattern detection, rate limit counting, and approval cache TTL.

## Coding Standards

- **Style:** PEP 8, enforced with `ruff` or `flake8`
- **Type hints:** All function signatures must include type annotations
- **Docstrings:** Google-style — every public function needs `Args:` and `Returns:` sections
- **Output:** All CLI output is structured JSON (stdout for data, stderr for errors)
- **No external dependencies:** This skill uses only Python stdlib (sqlite3, re, argparse, etc.)

## Making Changes

1. **Policy changes** — Edit `policies.json` directly. No code changes needed for new rules, patterns, or contacts.
2. **New scan patterns** — Add regex to `sensitive_patterns` in `policies.json`.
3. **New CLI commands** — Add a `cmd_<name>` function, register in `_DISPATCH` and `build_parser()`.
4. **Schema changes** — Append to `_SCHEMA_SQL` (SQLite is append-only for migrations).

## PR Process

1. Branch from `main` with a descriptive name (`fix/guardrails-rate-limit`, `feat/guardrails-new-pattern`)
2. Ensure all JSON output contracts remain backward-compatible
3. Update `SKILL.md` if adding or changing commands
4. Update `CHANGELOG.md` under an `[Unreleased]` section
5. Test manually with the commands above
6. Commit with conventional commits (`feat:`, `fix:`, `docs:`)
