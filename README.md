# OpenClaw Skills Workspace

Private skill library and workspace for OpenClaw AI agents. 25 skills across infrastructure, engineering, knowledge work, and domain expertise.

## Skills (25)

### Infrastructure (8)
| Skill | Description |
|-------|-------------|
| `agent-guardrails` | Safety gate for agent actions — policy enforcement, rate limiting, approval workflows |
| `agent-memory` | Shared brain — vector DB (SQLite + numpy), episodic/semantic/procedural memory |
| `agent-orchestration` | Multi-agent coordination, task routing, handoff protocols |
| `skill-creator-extended` | Autonomous skill generator — 4-phase pipeline (Research → Architecture → Implementation → Validation) + composition patterns |
| `skill-lifecycle` | Unified lifecycle management — Research→Build→Reflect evo loop + AIOps monitoring, circuit breakers, self-healing |
| `skill-scout` | Skill discovery, evaluation, and quarantine workflow |
| `cloudflare-deploy` | Deploy static sites to Cloudflare Pages — project management, deployment, status (stdlib-only Python) |
| `mailcow-manager` | Provision Hetzner VPS, install Mailcow, manage domains/mailboxes/DKIM, Cloudflare DNS (stdlib-only Python) |

### Engineering (5)
| Skill | Description |
|-------|-------------|
| `python-backend` | FastAPI, Django, Flask backend development |
| `web-builder` | Full web dev lifecycle — SvelteKit PWAs, single-file HTML bundling, GitHub Pages/Vercel deploy |
| `devops` | Complete DevOps — CI/CD, IaC, containers, Kubernetes, GitOps, progressive delivery |
| `security` | Unified security — appsec, vuln management, compliance, zero-trust, incident response, DevSecOps, threat modeling |
| `observability` | OpenTelemetry-first — structured logging, tracing, metrics, Prometheus/Grafana/Loki/Tempo, SLIs/SLOs, alert design |

### Knowledge Work (3)
| Skill | Description |
|-------|-------------|
| `docs-engine` | Documentation engine — Diátaxis scaffolding, GitHub Gold Standard templates, quality scoring |
| `email-manager` | Full IMAP/SMTP client for autonomous agents — structured JSON, priority detection, triage, threading |
| `task-planner` | Natural language task/project management — Kanban dashboard, file-based planning, workplace memory, daily planning |

### Domain Expertise (9)
| Skill | Description |
|-------|-------------|
| `legal` | Contract review, NDA triage, compliance (GDPR/CCPA/HIPAA), risk assessment, meeting briefings |
| `sales` | Prospecting, outreach, pipeline management, forecasting, battlecards, competitive analysis |
| `customer-support` | Ticket triage, escalation packaging, response drafting, KB article authoring |
| `product-management` | PRDs/feature specs, roadmaps, stakeholder updates, user research synthesis |
| `marketing` | Content creation, campaign planning, brand voice, SEO audits, competitive intel |
| `finance` | Journal entries, reconciliation, financial statements, variance analysis, close management |
| `data-analysis` | SQL (any dialect), EDA, dashboards, statistical analysis, data quality validation |
| `enterprise-search` | Unified cross-tool search — email, chat, docs, wikis with confidence scoring |
| `bio-research` | Literature review, scRNA-seq, sequencing pipelines, drug discovery, target prioritization |

## Cross-Skill Integration

9 integration pipelines connect skills into cross-functional workflows. See [docs/SKILL-INTEGRATION-ARCHITECTURE.md](docs/SKILL-INTEGRATION-ARCHITECTURE.md).

Key patterns:
- **Shared Brain**: `agent-memory` ↔ all skills (P0)
- **Deal Review**: `legal` + `sales` + `finance` (parallel → merge)
- **Product Launch**: `PM` → `marketing` → `sales` → `support` (sequential)
- **Research Chain**: `support` → `enterprise-search` → `email-manager` (cascading)

## Projects

| Project | Location | Status |
|---------|----------|--------|
| **TØrr Statics** | `torr-statics-site/` → [torrstatics.com](https://torrstatics.com) | Live (v3.5) |
| **MPMP** | `mpmp/` → [github.com/clawbotai/mpmp](https://github.com/clawbotai/mpmp) | Phase 1-6 complete |

## Shared Libraries

| Library | Purpose |
|---------|---------|
| `lib/memory_client.py` | Subprocess wrapper for agent-memory |
| `lib/guardrails_client.py` | Subprocess wrapper for agent-guardrails |

## Monitored Execution

All skill scripts route through `bin/skillrun` for error capture, classification, and self-healing:

```bash
bin/skillrun <skill-name> -- <command...>
```

## Attribution

Domain expertise skills (legal, sales, customer-support, product-management, marketing, finance, data-analysis, enterprise-search, bio-research) derived from [Anthropic knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) (Apache-2.0).
