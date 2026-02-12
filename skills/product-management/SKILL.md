---
name: product-management
description: Full PM workflow — feature specs/PRDs, roadmaps, stakeholder communication, user research synthesis, competitive analysis, and metrics tracking. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Product Management

Full PM workflow: writing feature specs and PRDs, managing roadmaps, communicating with stakeholders, synthesizing user research, analyzing competitors, and tracking product metrics.

## Activation Triggers

Activate when the user's request involves:
- Writing PRDs, feature specs, or requirements
- Roadmap planning, prioritization, or sequencing
- Stakeholder updates or status reports
- User research synthesis or feedback analysis
- Competitive analysis or market research
- Product metrics, KPIs, or OKRs

## Commands

### `/pm:write-spec`
Generate structured PRD from problem statement or feature idea.

**Structure:** Problem Statement (not solution statement) → User Stories (As a [user], I want [capability] so that [benefit]) → Requirements (MoSCoW: Must/Should/Could/Won't) → Success Metrics (measurable) → Scope (explicit in/out) → Technical Considerations (without prescribing implementation) → Dependencies → Open Questions

### `/pm:roadmap-update`
Create/update/reprioritize roadmap. Formats: Now/Next/Later, Quarterly Themes, OKR-aligned.

**Prioritization frameworks:** RICE (Reach, Impact, Confidence, Effort), ICE (Impact, Confidence, Ease), Weighted Scoring, Kano Model (Must-have, Performance, Delighter).

### `/pm:stakeholder-update`
Status updates tailored to audience:
- **Executive**: Strategic impact, metrics, decisions needed, timeline
- **Engineering**: Technical requirements, acceptance criteria, dependencies, priorities
- **Sales**: Customer impact, competitive positioning, timeline, talking points
- **Customer**: Benefits, timeline, migration plan if applicable

Formats: weekly, monthly, launch, ad-hoc.

### `/pm:synthesize-research`
Synthesize user research (interviews, surveys, feedback) into actionable insights.

**Qualitative:** Affinity mapping, thematic analysis, pattern recognition.
**Quantitative:** Survey analysis, NPS interpretation, usage analytics.
**Combined:** Triangulation for high-confidence insights.
**Output:** Insight statements, supporting evidence, confidence levels, prioritized recommendations.

### `/pm:competitive-analysis`
Research competitors: feature comparisons, positioning analysis, strategic implications.

## Auto-Firing Skills

### Spec Writing
**Fires when:** User discusses features, requirements, or product planning.

### Roadmap Planning
**Fires when:** User discusses roadmap, priorities, or strategic planning.

### Stakeholder Communication
**Fires when:** User asks about updates, status reports, or presentations.

### User Research Synthesis
**Fires when:** User mentions research, interviews, surveys, or feedback.

### Metrics Analysis
**Fires when:** User asks about product metrics, KPIs, or feature adoption.
Framework: Acquisition (signups, activation) → Engagement (DAU/MAU, feature adoption) → Retention (cohort analysis, churn) → Revenue (ARPU, expansion). OKR formulation, leading vs. lagging indicators.

## Configuration

```yaml
product_name: ""       # Product name and details
team_structure: {}     # Org chart with roles
okrs: []               # Current OKRs and strategic priorities
roadmap_format: "now-next-later"  # Preferred format
spec_template: ""      # Organization's PRD template
update_cadence: {}     # Stakeholder update schedule
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Project Management (Linear/Jira) | Features, sprints, roadmap | User provides details |
| Chat (Slack) | Team discussions, feedback | User provides context |
| Knowledge Base (Notion) | Specs, research, notes | User provides docs |
| Design (Figma) | Design files, prototypes | User describes designs |
| Analytics (Amplitude) | Usage data, adoption metrics | User provides data |
| Transcripts (Fireflies) | Interview recordings | User provides notes |
| Ticketing (Intercom) | Customer feedback patterns | User provides feedback |
