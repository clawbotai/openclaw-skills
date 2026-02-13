# Skill Integration Architecture

## Overview

This document defines concrete integration points between OpenClaw's 25 skills. Each integration is a typed interface — a contract between skills that enables cross-functional workflows without creating hard dependencies.

## Integration Layer Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     SHARED BRAIN                                │
│                  agent-memory (vector DB)                        │
│  Every skill reads/writes episodic + semantic memory            │
│  Connector: lib/memory_client.py (subprocess wrapper)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────────┐
│                   SAFETY GATE                                    │
│                agent-guardrails                                  │
│  External-facing actions pass through guardrails                │
│  Connector: lib/guardrails_client.py                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────────┐
│              CROSS-SKILL MESSAGE BUS                             │
│  Skills communicate via structured JSON on stdin/stdout          │
│  Schema: { skill, action, payload, context, trace_id }          │
└─────────────────────────────────────────────────────────────────┘
```

## Message Bus Protocol

Every cross-skill invocation follows this schema:

```json
{
  "skill": "email-manager",
  "action": "search",
  "payload": { "query": "invoice from Acme", "limit": 5 },
  "context": { "trace_id": "uuid", "caller": "enterprise-search", "user_role": "provider" },
  "response": { "status": "ok", "results": [] }
}
```

Skills don't import each other. They communicate through the agent (the LLM reads one skill's output and feeds it as input to another). The message bus is a *convention*, not a runtime.

---

## Integration Map

### 1. Enterprise Search → Email Manager

**Pattern:** Sequential
**Trigger:** `/search:search` query that could have email results

```
User: "Find the contract renewal discussion with Acme"
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│ enterprise-     │────▶│ email-manager   │────▶│ Synthesize   │
│ search          │     │ search --query   │     │ with other   │
│ (decompose      │     │ "Acme contract   │     │ source       │
│  query)         │     │  renewal"        │     │ results      │
└─────────────────┘     └─────────────────┘     └──────────────┘
```

**Interface:**
```
enterprise-search CALLS email-manager:
  Input:  email_client.py search --query "{query}" --limit 10
  Output: JSON array of { uid, from, subject, date, snippet }
  Merge:  Add to unified results with source="email", score by recency
```

**Implementation:** In enterprise-search's source management skill, add email-manager as a searchable source. When the agent detects enterprise-search is active and email is a configured source, it runs the email search command and feeds results back into the synthesis step.

---

### 2. Data Analysis → Finance

**Pattern:** Sequential
**Trigger:** `/finance:variance-analysis` or `/finance:financial-statements` with raw data

```
User: "Analyze Q4 budget vs actual variances"
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│ data-analysis   │────▶│ finance         │────▶│ Narrative    │
│ /data:write-    │     │ variance-       │     │ report with  │
│  query          │     │ analysis        │     │ root causes  │
│ (extract data)  │     │ (interpret)     │     │              │
└─────────────────┘     └─────────────────┘     └──────────────┘
```

**Interface:**
```
finance CALLS data-analysis:
  Input:  Natural language data request → SQL generation → execution
  Output: Structured dataset (CSV/JSON table)
  Handoff: finance receives data, applies accounting standards, generates variance narrative

data-analysis CALLS finance:
  Input:  "What accounting standard applies to this revenue recognition?"
  Output: ASC 606 guidance, proper categorization
  Handoff: data-analysis applies correct metric definitions from finance's chart of accounts
```

**Shared config:**
```yaml
# finance/config.yaml references data-analysis
data_source:
  warehouse_dialect: "postgresql"  # from data-analysis config
  chart_of_accounts: {}            # finance provides to data-analysis for column mapping
```

---

### 3. Customer Support → Task Planner

**Pattern:** Sequential (escalation → task creation)
**Trigger:** `/support:escalate` creates a tracked task

```
User: "Escalate this P1 to engineering"
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│ customer-       │────▶│ task-planner    │────▶│ Tracked      │
│ support         │     │ add_task        │     │ escalation   │
│ /support:       │     │ (P1, assigned   │     │ with         │
│  escalate       │     │  to eng)        │     │ deadline     │
│ (package)       │     │                 │     │              │
└─────────────────┘     └─────────────────┘     └──────────────┘
```

**Interface:**
```
customer-support CALLS task-planner:
  Input:  { title, priority, assignee, description, deadline, tags: ["escalation", "P1"] }
  Output: task_id, project assignment
  Script: task_planner/scripts/task_manager.py add --project "Escalations" --priority P1 --title "..."

customer-support CALLS task-planner (reverse):
  Input:  "What open P1 escalations do we have?"
  Output: Filtered task list from escalations project
```

---

### 4. Legal → Sales (Deal Review Composition)

**Pattern:** Parallel → Merge
**Trigger:** User says "review this deal" or "prep for contract negotiation"

```
User: "Review the Acme deal before signing"
         │
    ┌────┴────────────────┐
    ▼                     ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│ legal    │      │ sales    │      │ finance  │
│ /legal:  │      │ /sales:  │      │ (rev rec │
│ review-  │      │ call-    │      │  check)  │
│ contract │      │ prep     │      │          │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │
     └────────┬────────┘──────────────────┘
              ▼
     ┌──────────────┐
     │ UNIFIED DEAL │
     │ REVIEW BRIEF │
     │ Legal: G/Y/R │
     │ Sales: strat │
     │ Finance: rev │
     └──────────────┘
```

**Interface:**
```
Agent orchestrates three parallel skill invocations:
  1. legal/review-contract → clause analysis (G/Y/R)
  2. sales/call-prep → deal strategy, competitive position
  3. finance/accounting-standards → revenue recognition assessment

Merge: Combined brief with sections from each skill, conflicts flagged
```

---

### 5. Product Management → Marketing → Sales (Product Launch)

**Pattern:** Sequential pipeline
**Trigger:** User says "plan the launch for [feature]"

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ PM       │────▶│ Marketing│────▶│ Sales    │────▶│ Support  │
│ write-   │     │ plan-    │     │ battle-  │     │ write-kb │
│ spec     │     │ campaign │     │ card     │     │          │
│          │     │          │     │          │     │          │
│ PRD with │     │ Campaign │     │ Compete  │     │ KB       │
│ features │     │ plan +   │     │ card +   │     │ articles │
│ + metrics│     │ content  │     │ outreach │     │ for FAQ  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

**Interface:**
```
Each skill receives the prior skill's output as context:
  PM → { feature_name, value_props, target_audience, success_metrics }
  Marketing receives PM output → { campaign_plan, content_calendar, messaging }
  Sales receives PM + Marketing → { battlecard, outreach_templates, objection_handling }
  Support receives all → { kb_articles, FAQ, known_limitations }
```

---

### 6. Agent Memory → All Domain Skills

**Pattern:** Shared brain (read/write)
**Trigger:** Any skill activation checks memory for relevant context

```
┌─────────────────────────────────────────────┐
│              agent-memory                    │
│  ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │Episodic │ │Semantic │ │Procedural    │  │
│  │(events) │ │(facts)  │ │(how-to)      │  │
│  └────┬────┘ └────┬────┘ └──────┬───────┘  │
└───────┼───────────┼─────────────┼───────────┘
        │           │             │
   ┌────┴───┐  ┌───┴────┐  ┌────┴─────┐
   │ legal  │  │ sales  │  │ finance  │
   │remembers│  │remembers│  │remembers │
   │past     │  │deal    │  │close     │
   │reviews  │  │history │  │patterns  │
   └────────┘  └────────┘  └──────────┘
```

**Interface for all skills:**
```python
# Before any skill activation, agent checks memory:
memory_client.py search --query "{skill_context}" --type semantic --limit 3

# After skill produces output worth remembering:
memory_client.py store --type episodic --text "{summary}" --tags "{skill_name}"
```

**Skill-specific memory patterns:**
| Skill | Reads | Writes |
|-------|-------|--------|
| legal | Prior contract reviews for same vendor | Review results, playbook deviations |
| sales | Deal history, past interactions with account | Call notes, pipeline changes |
| customer-support | Known issues, past tickets for customer | Resolved patterns, new KB entries |
| finance | Prior period close notes, recurring accruals | Variance explanations, audit notes |
| data-analysis | Schema documentation, past query patterns | Dataset profiles, validated metrics |
| product-management | Past spec decisions, research findings | Spec versions, roadmap changes |

---

### 7. Customer Support → Enterprise Search → Email Manager (Research Chain)

**Pattern:** Cascading search
**Trigger:** `/support:research` needs to find answers across all sources

```
User: "Customer says feature X is broken after update"
         │
         ▼
┌─────────────────┐
│ customer-       │
│ support         │
│ /support:       │
│  research       │
│  (decompose)    │
└────────┬────────┘
         │ "search for feature X issues"
         ▼
┌─────────────────┐     Searches:
│ enterprise-     │────▶ 1. email-manager (customer threads)
│ search          │────▶ 2. task-planner (open bugs)
│ /search:search  │────▶ 3. web search (known issues)
└────────┬────────┘
         │ unified results with confidence scores
         ▼
┌─────────────────┐
│ customer-       │
│ support         │
│ /support:       │
│  draft-response │
│ (from research) │
└─────────────────┘
```

---

### 8. Security → DevOps → Observability (Incident Pipeline)

**Pattern:** Sequential with parallel enrichment
**Trigger:** Security incident detected or reported

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ security │────▶│ devops   │────▶│ observe  │
│ (threat  │     │ (contain │     │ (trace   │
│  assess) │     │  deploy) │     │  analyze)│
└──────────┘     └──────────┘     └──────────┘
     │                                  │
     └──────────► legal ◄──────────────┘
                (compliance obligations)
```

---

### 9. Bio Research → Data Analysis (Genomics Pipeline)

**Pattern:** Sequential
**Trigger:** `/bio:analyze-scrna` or `/bio:run-pipeline` produces data needing statistical analysis

```
bio-research                    data-analysis
┌──────────────┐               ┌──────────────┐
│ scRNA-seq    │──── data ────▶│ statistical  │
│ QC + cluster │               │ analysis     │
│              │               │ (DE genes,   │
│              │◀── results ──│  enrichment) │
└──────────────┘               └──────────────┘
```

---

## Implementation Priority

| # | Integration | Effort | Impact | Priority |
|---|-------------|--------|--------|----------|
| 1 | agent-memory → all skills | Medium | Very High | **P0** — foundation for everything |
| 2 | enterprise-search → email-manager | Low | High | **P1** — email is primary data source |
| 3 | customer-support → task-planner | Low | High | **P1** — escalation tracking |
| 4 | data-analysis → finance | Low | Medium | **P2** — variance analysis pipeline |
| 5 | legal + sales + finance (deal review) | Medium | High | **P2** — flagship composition |
| 6 | PM → marketing → sales (launch) | Medium | Medium | **P3** — impressive but less frequent |
| 7 | support → search → email (research) | Medium | High | **P2** — customer resolution speed |
| 8 | security → devops → observability | Low | Medium | **P3** — incident response |
| 9 | bio-research → data-analysis | Low | Low | **P4** — niche use case |

## Implementation Notes

1. **No hard dependencies.** Skills never import each other. The agent (LLM) is the integration layer — it reads one skill's output and routes it to another.

2. **Memory is the backbone.** agent-memory as shared brain (P0) enables every other integration. Without it, skills are stateless silos.

3. **Guardrails gate external actions.** Any integration that sends data externally (email, API calls, deployments) passes through agent-guardrails first.

4. **Configuration cross-references.** Skills can reference each other's config values. Example: finance's `chart_of_accounts` is available to data-analysis for column mapping.

5. **Trace IDs for composition.** When multiple skills collaborate on a single user request, they share a `trace_id` so agent-memory can reconstruct the full workflow later.

---

## Implementation Status

### Wired (code-level integration)
- ✅ **email-manager** → guardrails (scan before send, check tier) + memory (log sends, store urgent triage)
- ✅ **skill-lifecycle** → memory (store fix histories via run_monitored.py)
- ✅ **lib/memory_client.py** → thin subprocess wrapper for agent-memory
- ✅ **lib/guardrails_client.py** → thin subprocess wrapper for agent-guardrails
- ✅ **lib/integration.py** → composed workflows (safe_send_email, unified_search, customer_research, deal_review_context)

### Wired (instruction-level integration in SKILL.md)
All 25 skills now have Cross-Skill Integration sections documenting:
- Memory protocol (recall before, remember after)
- Safety gate (scan/check before external actions)
- Connected skills (which skills feed into/from this one)

### Protocol
See `lib/INTEGRATION-PROTOCOL.md` for the agent-followed integration protocol.

### Pre-Built Compositions
See `skills/agent-orchestration/SKILL.md` → Pre-Built Compositions section for:
- Deal Review (Expert Panel)
- Product Launch (Pipeline)
- Incident Response (Supervisor)
- QBR Preparation (Fan-Out/Fan-In)
- Customer Research (Cascade)
- Skill Factory (Pipeline)
