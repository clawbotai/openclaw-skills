---
name: customer-support
description: Support co-pilot — ticket triage, escalation management, response drafting, customer research with confidence scoring, and KB article authoring. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Customer Support

Ticket triage, escalation management, response drafting, customer research, and knowledge base authoring. Categorize issues, research answers across sources with confidence scoring, draft professional responses, package escalations for engineering, and convert resolved issues into KB articles.

## Activation Triggers

Activate when the user's request involves:
- Customer ticket or support request triage
- Drafting customer responses
- Escalating issues to engineering/product
- Researching customer questions across sources
- Writing knowledge base articles from resolved issues
- Support metrics or queue management

## Commands

### `/support:triage`
Analyze incoming ticket: categorize issue, assess priority, identify product area, recommend routing, suggest initial response.

**Categories:** Bug, Feature Request, How-To, Account/Billing, Integration, Performance, Security.
**Priority (P1-P4):** Factors: customer tier (enterprise > pro > free), feature criticality (core > secondary > cosmetic), blast radius (widespread > isolated), data integrity risk, SLA obligations.

### `/support:research`
Research customer question across all sources (docs, KB, previous tickets, web) with confidence-scored synthesis.

**Confidence scoring:** High (official docs, multiple confirmations), Medium (single authoritative source), Low (forum posts, outdated docs, unverified).

### `/support:draft-response`
Draft professional response tailored to situation, urgency, and channel.

**Framework:** Acknowledge (never dismiss) → Explain clearly (avoid jargon) → Set expectations (realistic timelines) → Provide next steps (concrete actions).
**Tone:** Match urgency, never defensive, use "we" language. Channel-specific: email (formal, structured), chat (brief, formatted, links), social (concise, move to private).

### `/support:escalate`
Package ticket for engineering escalation: Summary (one paragraph), Customer Impact (accounts, revenue, SLA), Technical Details (errors, logs, repro steps), Business Context (relationship, contract, renewal), Requested Action, Timeline. Include everything engineering needs without back-and-forth.

### `/support:write-kb`
Convert resolved issue into KB article to reduce future ticket volume.

## Auto-Firing Skills

### Ticket Triage
**Fires when:** User provides a customer issue or bug report.

### Response Drafting
**Fires when:** User needs to write a customer reply.

### Escalation Packaging
**Fires when:** User needs to escalate to engineering or management.

### Knowledge Synthesis
**Fires when:** User asks a question requiring multi-source research.
Methodology: search all sources in parallel, score by recency/authority, deduplicate, synthesize, attribute sources, flag conflicts.

## Configuration

```yaml
product_areas: []      # Product areas for routing
priority_matrix: {}    # Custom priority definitions and SLA timelines
escalation_paths: {}   # Routing rules: which teams handle which issues
tone_guidelines: ""    # Customer communication style guide
known_issues: []       # Current known issues for quick triage matching
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Ticketing (Zendesk/Intercom) | Ticket data, customer history | User provides ticket text |
| CRM (HubSpot) | Account details, plan info | User provides customer context |
| Knowledge Base (Guru/Notion) | Documentation, SOPs | Web search + built-in frameworks |
| Project Tracker (Jira) | Bug tracking, escalations | Manual escalation drafting |
| Chat (Slack) | Internal discussions | User provides context |
