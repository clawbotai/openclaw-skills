# Changelog

All notable changes to the **agent-guardrails** skill are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-02-11

### Added

- **4-tier risk classification** (T1 Safe → T4 High) with policy-driven rule matching
- **Tier promotion engine** — auto-promotes actions based on sensitive paths, sudo usage, `rm -rf` detection, unknown recipients, and quiet hours
- **Sensitive data scanner** — regex-based detection of API keys (AWS, OpenAI, GitHub), PII (SSNs, credit cards, phone numbers, emails), private key blocks, and passwords
- **Prompt injection detection** — pattern matching against configurable injection signatures in external content
- **Session approval cache** — auto-approves repeated same-action+target within a configurable TTL (default 5 min) to reduce user fatigue; T4 actions are never cached
- **Rate limiting** — per-tier rate limits (T3: 5/min, T4: 3/hr) enforced via SQLite audit trail
- **SQLite audit trail** with WAL mode — every T2+ decision is logged with action, target, tier, decision, reason, and session
- **Audit query CLI** — filter audit entries by tier, action, date range, with configurable limits
- **Health report** (`stats`) — tier counts, decision breakdown, current rate usage, recent denials, DB size
- **File snapshot system** (`snapshot.py`) — save/restore/list/prune file snapshots before modification, with 100 MB size guard and JSON sidecar metadata
- **Configurable policies** via `policies.json` — known contacts, sensitive paths, custom patterns, quiet hours, rate limits
- **Sub-agent safety boundary** — documented max-tier T2 constraint for sub-agents
