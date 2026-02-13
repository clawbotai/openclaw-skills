---
name: customer-support
description: Support co-pilot — ticket triage, escalation management, response drafting, customer research with confidence scoring, and KB article authoring. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Customer Support

Ticket triage, customer research, response drafting, escalation packaging, and knowledge base authoring. Every response includes confidence scoring so the agent knows when to escalate vs resolve autonomously.

## Activation Triggers

Activate when the user's request involves:
- Customer tickets, complaints, or inquiries
- Drafting support responses
- Escalating issues to engineering or management
- Writing or updating knowledge base articles
- Customer sentiment analysis or satisfaction tracking
- Support queue management or triage

## Commands

### `/support:triage`
Classify and prioritize an incoming ticket.

**Workflow:**
1. **Parse** — extract: customer name, product, issue type, sentiment, urgency signals
2. **Classify** — category (bug, feature request, billing, how-to, account, outage)
3. **Prioritize** — P1 (outage/data loss), P2 (broken feature, workaround exists), P3 (minor issue), P4 (question/enhancement)
4. **Check history** — known issue? Duplicate? Related tickets?
5. **Route** — assign to correct team/individual based on category and skill
6. **SLA clock** — set response deadline based on priority and customer tier

**Priority matrix:**
| Impact \ Urgency | Blocking | Degraded | Inconvenience |
|-------------------|----------|----------|---------------|
| **Multiple users** | P1 | P1 | P2 |
| **Single user** | P2 | P3 | P4 |
| **No workaround** | P1 | P2 | P3 |

### `/support:research`
Research a customer's issue across all available sources.

**Workflow:**
1. **Customer profile** — account age, plan tier, past tickets, NPS score
2. **Issue history** — similar tickets, known bugs, recent changes
3. **Technical context** — relevant logs, error codes, system status
4. **KB search** — existing articles that may resolve
5. **Confidence score** — rate confidence in root cause (0.0–1.0)
   - ≥0.8: Resolve autonomously with standard response
   - 0.5–0.8: Draft response, flag for human review
   - <0.5: Escalate with research notes

### `/support:draft-response`
Draft a customer response.

**Workflow:**
1. **Acknowledge** — confirm understanding of the issue (mirror their language)
2. **Explain** — root cause in customer-friendly terms (no jargon)
3. **Resolve** — step-by-step instructions or fix confirmation
4. **Prevent** — what we're doing to prevent recurrence (if applicable)
5. **Close** — next steps, follow-up timeline, satisfaction check

**Tone rules:**
- Match customer's formality level
- Never blame the customer
- Never say "Unfortunately" — reframe positively
- Specific > vague ("by Friday 5pm" not "soon")
- One action per sentence in instructions

### `/support:escalate`
Package an escalation for engineering or management.

**Workflow:**
1. **Summary** — one-sentence issue description
2. **Impact** — users affected, revenue at risk, SLA status
3. **Timeline** — when reported, when reproduced, current status
4. **Technical details** — steps to reproduce, error messages, logs, environment
5. **What's been tried** — troubleshooting steps taken and results
6. **Customer context** — tier, sentiment, history, churn risk
7. **Recommended action** — specific ask (fix, workaround, communication)
8. **Create task** — auto-create tracked task via task-planner integration

### `/support:write-kb`
Author a knowledge base article.

**Workflow:**
1. **Identify need** — repeated question (3+ tickets) or new feature documentation
2. **Structure** — title, problem statement, solution steps, prerequisites, related articles
3. **Write** — clear, scannable (numbered steps, bold key actions, screenshots referenced)
4. **Validate** — test steps against current product version
5. **Metadata** — tags, category, product version, last verified date
6. **Review** — flag for SME review if technical depth requires it

## Auto-Firing Skills

### Ticket Triage Intelligence
**Fires when:** New ticket or customer message arrives.
Auto-classify sentiment (positive/neutral/frustrated/angry), detect urgency signals ("down", "broken", "ASAP", "losing money"), identify VIP customers, check for duplicate/related tickets.

### Response Quality
**Fires when:** Drafting any customer-facing response.
Checklist: addresses all points raised, correct grammar/spelling, appropriate tone, no internal jargon leaked, includes next steps, response length appropriate (concise for simple, detailed for complex).

### Escalation Packaging
**Fires when:** Issue needs engineering involvement.
Ensure: reproducible steps included, environment details captured, customer impact quantified, SLA deadline noted, severity correctly assessed. Never escalate without troubleshooting first.

### Knowledge Synthesis
**Fires when:** Resolving a ticket reveals undocumented information.
Trigger KB article creation when: same question asked 3+ times, workaround discovered for known bug, new feature launched without docs, common misconfiguration identified.

## Configuration

```yaml
sla_response_hours:
  P1: 1
  P2: 4
  P3: 24
  P4: 48
customer_tiers:
  enterprise: { priority_boost: 1, dedicated_rep: true }
  pro: { priority_boost: 0, dedicated_rep: false }
  free: { priority_boost: -1, dedicated_rep: false }
auto_resolve_confidence: 0.8    # Minimum confidence for autonomous resolution
escalation_targets:
  engineering: ""               # Channel/email for eng escalations
  billing: ""                   # Channel/email for billing issues
  management: ""                # Channel/email for P1 or VIP issues
kb_duplicate_threshold: 3       # Tickets before triggering KB article
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Helpdesk (Zendesk/Intercom/Freshdesk) | Ticket management | Manual ticket tracking in task-planner |
| CRM (Salesforce/HubSpot) | Customer profile, account data | User provides customer context |
| Knowledge Base (Notion/Confluence) | KB articles, internal docs | Maintain KB as markdown files |
| Chat (Slack/Discord) | Internal escalation channels | Email escalation or task creation |
| Analytics (Mixpanel/Amplitude) | Usage data for debugging | User describes customer behavior |
