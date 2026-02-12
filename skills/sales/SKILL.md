---
name: sales
description: Sales productivity — prospecting, outreach, pipeline management, call preparation, deal strategy, competitive analysis, and forecasting. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Sales

Sales productivity skill for prospecting, outreach, pipeline management, call preparation, deal strategy, and competitive analysis. Works standalone with web search and user input, supercharged when connected to CRM, email, and enrichment tools.

## Activation Triggers

Activate when the user's request involves:
- Prospecting, account research, or lead qualification
- Drafting sales emails, LinkedIn messages, or outreach
- Pipeline review, deal strategy, or forecasting
- Call preparation or meeting follow-up
- Competitive analysis or battlecards
- Sales metrics or win/loss analysis

## Commands

### `/sales:call-prep`
Comprehensive call preparation: company research, attendee profiles, talking points, objections, recommended questions. Supports discovery, demo, negotiation, and executive briefings.

### `/sales:pipeline-review`
Analyze pipeline health: deal prioritization, risk flags (stale deals, past close dates, single-threaded), weekly action plan. Accepts CSV, pasted data, or CRM connection.

**Risk signals:** No next step, stage duration > 1.5× average, pushed close dates, champion departure, single-threaded.

### `/sales:forecast`
Weighted forecast: best/likely/worst scenarios, commit vs. upside breakdown, gap analysis. Coverage ratio target: 3-4× quota.

### `/sales:call-debrief`
Process call notes/transcript: extract action items, draft follow-up email, generate internal summary. Log to CRM if connected.

### `/sales:draft-outreach`
Research prospect first, then generate personalized outreach with multiple angles. Supports cold email, LinkedIn, follow-up, re-engagement.

**Best practices:** Personalize beyond first name, lead with insight not pitch, cold emails < 150 words, single CTA, no attachments on first touch. Email: subject < 50 chars, send Tue-Thu 8-10am recipient TZ. LinkedIn: connect request < 300 chars, no pitch in connection request.

### `/sales:battlecard`
Competitive battlecard: feature comparison, positioning, objection handling, win/loss themes.

## Auto-Firing Skills

### Account Research
**Fires when:** User asks to research a company/prospect.
Methodology: company overview, key contacts, recent news (<90 days), tech stack, hiring signals, competitive landscape. Cross-reference multiple sources.

### Pipeline Analysis
**Fires when:** User discusses pipeline, deals, or sales metrics.
Health indicators: coverage ratio, velocity (avg days/stage), conversion rates, deal size trends, win/loss analysis.

### Sales Asset Generation
**Fires when:** User asks for sales collateral.
Generate custom assets: landing pages, decks, one-pagers, ROI calculators. Reference prospect's specific pain points and competitive differentiation.

## Configuration

```yaml
name: ""              # Rep's name for outreach personalization
title: ""             # Rep's title
company: ""           # Organization name and details
quota: {}             # Annual and quarterly quota numbers
product: {}           # Product name, value props, competitor list
messaging_framework: {} # Approved messaging, brand voice, positioning
sales_stages: []      # Custom pipeline stages with duration and exit criteria
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| CRM (HubSpot/Salesforce) | Deal data, contacts, pipeline | User provides deal details |
| Enrichment (Clay/ZoomInfo) | Company/contact enrichment | Web search for research |
| Chat (Slack) | Deal discussions, competitive intel | User provides context |
| Transcripts (Gong) | Call recordings and follow-up | User provides call notes |
| Knowledge Base (Notion) | Playbooks, competitive intel, docs | Built-in frameworks |
| Email/Calendar (M365) | Correspondence, scheduling | User provides details |
