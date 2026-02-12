---
name: enterprise-search
description: Unified cross-tool search — one query searches email, chat, documents, wikis, and project trackers simultaneously with source attribution and confidence scoring. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Enterprise Search

Search across all company tools in one place. Decomposes questions, runs targeted searches across every source, and synthesizes results into a single coherent answer with source attribution.

## Activation Triggers

Activate when the user's request involves:
- Finding information across multiple tools
- "Where did we discuss...", "What was decided about..."
- Cross-tool search or unified lookup
- Activity digests or periodic summaries

## Commands

### `/search:search`
Search all connected sources for a query. Decompose question → search each source → deduplicate → synthesize with attribution.

**Source priority:** Official docs > Email > Chat > Web.
**Conflict resolution:** When sources disagree, present both with timestamps. Let user determine authority.

### `/search:digest`
Periodic activity digest across all tools. Daily and weekly formats.

## Auto-Firing Skills

### Source Management
**Fires when:** Determining which sources to search.
Know which sources are available, guide users to connect new ones, handle rate limits. When a source is unavailable, state what might be missing.

### Knowledge Synthesis
**Fires when:** Multi-source results need combination.
Combine into coherent answers, deduplicate, attribute sources, score confidence by freshness and authority, summarize large result sets.

## Configuration

```yaml
source_priority: []    # Ranked sources by authority
search_scopes: {}      # Default scopes per query type
user_channels: []      # Subscribed channels for digest filtering
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Chat (Slack) | Conversations, channels, DMs | User provides context |
| Email (M365/Gmail) | Inbox, sent, threads | User searches manually |
| Cloud Storage (Notion/GDrive) | Documents, wikis | User provides docs |
| Knowledge Base (Guru/Confluence) | Internal docs, SOPs | Web search fallback |
| Project Tracker (Jira/Asana) | Tasks, issues, records | User provides details |
