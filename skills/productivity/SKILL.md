---
name: productivity
description: Task management, workplace memory, and visual dashboard — the AI learns people, projects, and terminology to act like a colleague, not a chatbot. TASKS.md-based tracking with two-tier memory. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Productivity

Task management, workplace memory, and a visual dashboard. The AI learns the user's people, projects, and terminology so it acts like a colleague, not a chatbot. Features markdown task list (TASKS.md), two-tier memory system, and local HTML dashboard.

## Activation Triggers

Activate when the user's request involves:
- Task management, to-dos, or action items
- Daily planning or weekly review
- Delegation or task assignment
- Dashboard or visual overview of work
- References to people, projects, or company jargon (workplace memory)

## Commands

### `/productivity:plan-day`
Generate daily plan from tasks, calendar, and priorities. Factor in energy management, meeting prep time, and focus blocks.

### `/productivity:weekly-review`
Weekly review: completed, slipped, upcoming priorities, inbox/task cleanup.

### `/productivity:delegate`
Draft delegation message: full context, specific ask, deadline, success criteria.

## Auto-Firing Skills

### Task Management
**Fires when:** User mentions tasks, to-dos, or action items.
TASKS.md pattern: add tasks from conversation, track status (pending/in-progress/done/blocked), triage stale items, sync with project trackers. Prioritization: Eisenhower matrix, time-boxing, dependency awareness.

### Workplace Memory
**Fires when:** Always active. Maintains persistent work context.

**Two-tier system:**
- **Tier 1 (Core)**: People (names, roles, nicknames, relationships), Projects (names, status, stakeholders), Terminology (jargon, acronyms, product names)
- **Tier 2 (Extended)**: Preferences (communication style, hours, tool preferences), History (past decisions, recurring patterns, constraints)

Example: "Ask Todd about the PSR for Oracle" → Todd Martinez is Finance lead, PSR = Pipeline Status Report, Oracle = Oracle Systems deal.

### Dashboard Generation
**Fires when:** User asks for visual overview or board view.
Generate self-contained HTML dashboard: task board (kanban/list), calendar summary, workplace context view, activity timeline. Works offline.

## Configuration

```yaml
workplace_context: {}  # People directory, project list, terminology
working_hours: {}      # Preferred hours and timezone
task_file_path: "TASKS.md"  # Path to persistent task file
communication_preferences: {} # Preferred channels by type
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Chat (Slack) | Team communications | User provides context |
| Knowledge Base (Notion) | Project docs, wikis | TASKS.md + memory |
| Project Tracker (Asana/Linear) | Task sync, status | TASKS.md standalone |
| Email/Calendar (M365) | Calendar, scheduling | User provides schedule |
