# Changelog

All notable changes to the **agent-memory** skill are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-02-11

### Added

- **3-tier memory architecture** — working (platform), episodic (timestamped events), and semantic (distilled facts) stored in SQLite with WAL mode
- **Vector embedding** via `sentence-transformers/all-MiniLM-L6-v2` (384-dim) with lazy-loaded singleton model for fast subsequent calls
- **Hybrid recall scoring** — weighted combination of cosine similarity (0.5), importance (0.3), and recency decay (0.2) using logarithmic time decay
- **Knowledge graph** — automatic edge creation between memories sharing entities and semantic similarity; explicit linking via `relate` command with custom relation types and weights
- **Graph expansion** — high-confidence recall results (score > 0.85) trigger neighbor retrieval from the graph, returned with `via_graph` metadata
- **Keyword fallback** — SQL LIKE search when the embedding model is unavailable, with importance + recency scoring
- **Entity extraction** — lightweight regex heuristic detecting proper nouns, ALL-CAPS acronyms, and CamelCase identifiers (no NLP dependencies)
- **Heuristic importance scoring** — auto-calculated from word count and entity richness, with manual override support
- **Soft-delete** (`forget`) — marks memories as decayed without physical deletion; excluded from all searches
- **Reflection cycle** (`reflect`) — prunes stale low-importance memories, detects near-duplicates (cosine > 0.95), promotes frequently-accessed episodic → semantic, and cleans orphan graph edges
- **Timeline retrieval** — chronological memory view with optional entity and date filters
- **Markdown import** (`import-md`) — splits markdown files by headings/double-newlines into chunks, embeds each, and stores with auto-importance
- **Full export** — JSON dump of all active memories and edges (without embeddings)
- **Health report** (`stats`) — instant (no model loading) report of counts, type distribution, importance histogram, staleness, and DB size
