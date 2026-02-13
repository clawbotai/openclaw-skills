---
name: product-management
description: Full PM workflow — feature specs/PRDs, roadmaps, stakeholder communication, user research synthesis, competitive analysis, and metrics tracking. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Product Management

Feature specs, roadmaps, stakeholder communication, user research synthesis, competitive analysis, and metrics tracking. Translates business problems into engineering-ready specifications.

## Activation Triggers

Activate when the user's request involves:
- Writing PRDs, feature specs, or user stories
- Roadmap planning or prioritization
- Stakeholder updates or communication
- User research synthesis or persona development
- Competitive product analysis
- Product metrics, KPIs, or OKRs
- Feature prioritization frameworks

## Commands

### `/pm:write-spec`
Write a PRD or feature specification.

**Template:**
1. **Problem Statement** — what user pain are we solving? Evidence (support tickets, research, data).
2. **Success Metrics** — how do we know this worked? Primary metric + guardrail metrics.
3. **User Stories** — "As a [persona], I want [action] so that [outcome]"
4. **Requirements** — must-have (P0), should-have (P1), nice-to-have (P2). Each with acceptance criteria.
5. **Non-Requirements** — explicit scope boundaries (what we're NOT building)
6. **Technical Considerations** — dependencies, API changes, data model impact, performance requirements
7. **Design** — wireframes reference, key interaction flows, edge cases
8. **Launch Plan** — rollout strategy (flag, %, full), monitoring, rollback criteria
9. **Open Questions** — unresolved decisions with owners and deadlines
10. **Timeline** — milestones with dates and dependencies

### `/pm:roadmap-update`
Update and communicate roadmap changes.

**Workflow:**
1. **Current state** — what shipped, what's in progress, what's planned
2. **Changes** — what moved, why (data-driven justification)
3. **Impact assessment** — who's affected by changes? Dependencies broken?
4. **Prioritization** — framework used (RICE, ICE, weighted scoring, opportunity sizing)
5. **Communication** — tailored message per audience (exec: strategy, eng: scope, sales: timeline)

**RICE scoring:**
| Factor | Definition | Scale |
|--------|-----------|-------|
| Reach | Users affected per quarter | Actual number |
| Impact | Effect per user | 3=massive, 2=high, 1=medium, 0.5=low, 0.25=minimal |
| Confidence | Evidence level | 100%=high, 80%=medium, 50%=low |
| Effort | Person-months | Actual estimate |

Score = (Reach × Impact × Confidence) / Effort

### `/pm:stakeholder-update`
Draft stakeholder communication.

**Formats by audience:**
- **Executive** — 3 bullets: progress, risk, ask. No details. Attach data.
- **Engineering** — scope changes, priority shifts, new requirements. Be specific.
- **Sales/CS** — timeline, customer-facing changes, talking points, FAQ
- **Board** — narrative: market context, strategy, metrics, outlook

### `/pm:synthesize-research`
Synthesize user research into actionable insights.

**Workflow:**
1. **Data collection** — interviews, surveys, analytics, support tickets, session recordings
2. **Coding** — tag themes, pain points, feature requests, workflows
3. **Pattern identification** — frequency analysis, segment differences, severity ranking
4. **Insights** — "We learned that [finding] because [evidence], which means [implication]"
5. **Recommendations** — prioritized list of actions with confidence levels
6. **Persona update** — refine personas based on new data

### `/pm:competitive-analysis`
Product competitive analysis.

**Framework:**
1. **Feature matrix** — feature-by-feature comparison (✓/partial/✗)
2. **Positioning map** — 2×2 matrix on key dimensions
3. **Pricing comparison** — plans, pricing model, value per tier
4. **User experience** — onboarding flow, key workflows, friction points
5. **Technical** — architecture, integrations, API quality, performance
6. **Market** — market share, growth trajectory, funding, team size
7. **Strategy implications** — where to compete, where to differentiate, where to concede

## Auto-Firing Skills

### Spec Writing
**Fires when:** User discusses features, requirements, or user problems.
Every spec needs: clear problem statement (not solution), measurable success criteria, explicit non-requirements, edge cases enumerated, launch/rollback plan.

### Roadmap Management
**Fires when:** User discusses priorities, timelines, or what to build next.
Maintain living roadmap. Challenge scope creep. Ensure every item has: owner, estimate, dependencies, success metric. Default to smaller scope shipped faster.

### Stakeholder Communication
**Fires when:** User needs to share updates or get alignment.
Tailor depth to audience. Executives want "so what?" not "what." Engineers want precision. Sales wants customer impact and dates. Never surprise stakeholders.

### Research Synthesis
**Fires when:** User shares interview notes, survey results, or usage data.
Separate observation from interpretation. Quantify when possible. Identify conflicting signals. Flag small sample sizes. Connect to existing product strategy.

### Metrics & OKRs
**Fires when:** User discusses goals, KPIs, or success measurement.
Good metrics: measurable, actionable, relevant, timely. Pair every vanity metric with a health metric. North Star metric + input metrics that drive it. Counter-metrics to prevent gaming.

## Configuration

```yaml
product_name: ""
team_members: []              # Name, role, capacity
roadmap_horizon: "quarter"    # quarter, half, year
prioritization_framework: "RICE"  # RICE, ICE, weighted, opportunity
sprint_length_weeks: 2
okr_cycle: "quarterly"
competitors: []               # Products to track
personas: []                  # User personas with descriptions
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Project Tracker (Linear/Jira) | Issues, sprints, velocity | Markdown specs and task-planner |
| Analytics (Amplitude/Mixpanel) | Usage data, funnels, retention | User provides data exports |
| Research (Dovetail/UserTesting) | Interview notes, recordings | User provides research notes |
| Design (Figma) | Wireframes, prototypes | Describe interactions in spec |
| Docs (Notion/Confluence) | PRDs, roadmaps, meeting notes | Markdown files in workspace |
