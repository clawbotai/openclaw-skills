---
name: enterprise-search
description: Unified cross-tool search — one query searches email, chat, documents, wikis, and project trackers simultaneously with source attribution and confidence scoring. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Enterprise Search

One query, every source. Decompose natural language queries into tool-specific searches, merge results with confidence scoring and source attribution, and synthesize actionable answers.

## Activation Triggers

Activate when the user's request involves:
- Finding information across multiple tools or sources
- "Where did we discuss..." or "Find the document about..."
- Cross-referencing information from different systems
- Building a complete picture from scattered data

## Commands

### `/search:search`
Unified search across all configured sources.

**Workflow:**
1. **Parse intent** — extract entities, time range, source hints from natural language
2. **Decompose** — generate tool-specific queries (email search syntax, Slack filters, wiki keywords)
3. **Execute** — run searches in parallel across configured connectors
4. **Score** — assign confidence (0.0–1.0) based on relevance, recency, source authority
5. **Deduplicate** — merge results referencing the same topic across sources
6. **Rank** — sort by composite score (relevance × recency × authority)
7. **Present** — unified results with source attribution, snippets, and direct links

**Output format:**
```
[0.92] 📧 Email — "Re: Acme contract renewal" (2026-02-10)
       From: Todd Martinez → Steven Reynolds
       "...agreed to extend terms through Q3 with 5% increase..."

[0.87] 💬 Slack — #deals channel (2026-02-08)
       Sarah: "Acme renewal is on track, Todd confirmed pricing"

[0.71] 📄 Docs — "Acme Partnership Agreement v3" (2026-01-15)
       Section 4.2: Renewal terms and pricing schedule
```

### `/search:digest`
Compile a topic digest — everything known about a subject across all sources, organized chronologically with key takeaways.

**Workflow:**
1. Run `/search:search` with broad query
2. Group results by subtopic and timeline
3. Identify contradictions or gaps
4. Synthesize narrative with citations
5. Flag stale information (>90 days)

## Auto-Firing Skills

### Source Management
**Fires when:** User mentions a new tool or data source.
Maintain a source registry with: name, type (email/chat/docs/wiki/tracker), search capabilities, authentication status, last successful query.

### Knowledge Synthesis
**Fires when:** Search returns results from 3+ sources.
Cross-reference for consistency. Flag contradictions (e.g., email says "deal closed" but tracker shows "in progress"). Highlight information decay (outdated docs vs recent conversations).

### Query Optimization
**Fires when:** Initial search returns poor results (<3 results or low confidence).
Reformulate: broaden terms, try synonyms, expand time range, check alternate sources. Report what was tried and why results are limited.

## Configuration

```yaml
sources:
  email:
    enabled: true
    connector: "email-manager"     # Uses email-manager skill
    search_method: "imap_search"
  chat:
    enabled: false
    connector: "slack"
    workspace: ""
  documents:
    enabled: false
    connector: "notion"
    workspace_id: ""
  tracker:
    enabled: false
    connector: "linear"
    team_id: ""
default_time_range: "90d"          # Default search window
max_results_per_source: 10
confidence_threshold: 0.3          # Minimum score to include
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Email (IMAP) | Search email threads | Uses email-manager skill directly |
| Chat (Slack/Discord) | Channel and DM search | User pastes relevant messages |
| Documents (Notion/Confluence) | Wiki and doc search | User provides document links |
| Tracker (Linear/Jira) | Issue and project search | User describes ticket status |
| Files (local filesystem) | Search workspace files | `grep`/`find` on workspace |
