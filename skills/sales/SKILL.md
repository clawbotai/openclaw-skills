---
name: sales
description: Sales productivity — prospecting, outreach, pipeline management, call preparation, deal strategy, competitive analysis, and forecasting. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Sales

Prospecting, outreach drafting, pipeline management, call preparation, deal strategy, competitive battlecards, and forecasting. Optimized for B2B sales cycles.

## Activation Triggers

Activate when the user's request involves:
- Prospecting or lead research
- Drafting outreach (cold email, follow-up, LinkedIn)
- Pipeline review or deal strategy
- Call preparation or debriefs
- Competitive analysis or battlecards
- Revenue forecasting

## Commands

### `/sales:call-prep`
Prepare for a sales call or meeting.

**Workflow:**
1. **Account research** — company size, industry, recent news, tech stack, funding
2. **Contact research** — role, tenure, LinkedIn activity, mutual connections, past interactions
3. **Deal context** — stage, history, open proposals, competitors mentioned
4. **Talking points** — 3 key value props tailored to their pain points
5. **Questions to ask** — discovery questions by stage (BANT/MEDDIC framework)
6. **Objection prep** — likely pushbacks and responses
7. **Goal** — specific outcome desired from this call

### `/sales:pipeline-review`
Review and clean pipeline.

**Workflow:**
1. **Snapshot** — total pipeline value by stage, weighted forecast
2. **Stale deals** — flag anything with no activity >14 days
3. **Stage accuracy** — verify deals are in correct stage (challenge optimism)
4. **Coverage ratio** — pipeline vs quota (target: 3x for new business, 2x for renewal)
5. **Risk assessment** — deals with single-threaded contacts, no next step, competitor present
6. **Recommendations** — specific actions per deal (advance, nurture, or disqualify)

### `/sales:forecast`
Revenue forecast with confidence bands.

**Workflow:**
1. **Committed** — signed contracts, POs in hand (95% confidence)
2. **Best case** — verbal commits, final negotiation (60-80%)
3. **Pipeline** — qualified opportunities by weighted stage probability
4. **Upside** — potential pull-forward from next quarter
5. **Risk adjustments** — historical close rates by rep, segment, deal size
6. **Gap analysis** — forecast vs quota, actions needed to close gap

### `/sales:call-debrief`
Capture notes and next steps after a call.

**Workflow:**
1. **Outcome** — what happened? (advanced/stalled/lost/discovery)
2. **Key learnings** — new information about pain, budget, timeline, decision process
3. **Stakeholder map update** — who was there, roles, influence, sentiment
4. **Objections raised** — and how they were handled
5. **Next steps** — specific actions with owners and deadlines
6. **Deal stage update** — should this move forward or back?

### `/sales:draft-outreach`
Draft personalized outreach.

**Types:** Cold email, follow-up, breakup email, LinkedIn message, intro request.

**Cold email framework:**
1. **Subject** — specific, curiosity-driven, <50 chars, no spam triggers
2. **Hook** — personalized observation (trigger event, mutual connection, specific insight)
3. **Value** — one sentence on relevant outcome you deliver
4. **Proof** — brief social proof (similar company, metric)
5. **CTA** — single, low-friction ask ("worth a 15-min call?")
6. **Length** — under 100 words. No attachments on first touch.

### `/sales:battlecard`
Competitive battlecard for a specific competitor.

**Sections:**
1. **Overview** — competitor positioning, target market, pricing model
2. **Strengths** — what they genuinely do well (be honest)
3. **Weaknesses** — validated gaps, not FUD
4. **Landmines** — questions to ask that expose their weaknesses
5. **Objection handling** — "Why not [competitor]?" responses
6. **Win stories** — brief case studies of wins against this competitor
7. **Trap plays** — requirements to include in RFPs that favor you

## Auto-Firing Skills

### Account Research
**Fires when:** User mentions a company or prospect name.
Pull: company website, LinkedIn, Crunchbase, recent news, job postings (signals growth/pain), tech stack (BuiltWith/Wappalyzer), financial data if public.

### Pipeline Analysis
**Fires when:** User discusses deals, quota, or forecast.
Apply MEDDIC (Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion) to assess deal health. Flag missing elements.

### Outreach Optimization
**Fires when:** User drafts any external communication.
Check: personalization (not generic), appropriate length, clear CTA, no spam trigger words, correct tone for relationship stage, follow-up timing (2-3 days for warm, 5-7 for cold).

## Configuration

```yaml
quota_amount: 0                # Quarterly/annual quota
pipeline_stages:
  - { name: "Discovery", probability: 10 }
  - { name: "Qualification", probability: 25 }
  - { name: "Proposal", probability: 50 }
  - { name: "Negotiation", probability: 75 }
  - { name: "Closed Won", probability: 100 }
  - { name: "Closed Lost", probability: 0 }
stale_deal_days: 14            # Days without activity before flagging
coverage_ratio_target: 3.0     # Pipeline/quota ratio
competitors: []                # Known competitor names
crm_connector: ""              # CRM system identifier
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| CRM (Salesforce/HubSpot) | Pipeline, accounts, contacts | Manual deal tracking in markdown |
| Email (Gmail/Outlook) | Outreach, thread history | Use email-manager skill |
| LinkedIn (Sales Navigator) | Prospect research, connections | Web search for prospects |
| Enrichment (ZoomInfo/Apollo) | Contact and company data | Manual web research |
| Calendar (Google/O365) | Meeting scheduling, call history | User provides schedule context |

## Cross-Skill Integration

### Memory Protocol
- **Before `/sales:call-prep`**: `memory.py recall "[sales] {company_name}"` — deal history, past interactions, stakeholder map
- **After `/sales:call-debrief`**: `memory.py remember "[sales] Call with {company}: {outcome}, next={action}" --importance 0.7`
- **After `/sales:pipeline-review`**: store stale deal flags and forecast snapshot
- **After `/sales:battlecard`**: store as semantic memory for reuse

### Safety Gate
- **Before `/sales:draft-outreach`**: `guardrails.py scan --text "{email_body}"` for leaked pricing/terms
- **Before sending outreach**: `guardrails.py check --action send_email --target {prospect}`

### Connected Skills
- **legal** → deal review: legal risk feeds into negotiation strategy
- **finance** → revenue recognition check before committing deal terms
- **enterprise-search** → pull all prior touchpoints with account from email + memory
- **marketing** → battlecard competitive intel feeds marketing competitive briefs
