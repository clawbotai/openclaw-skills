# agent-memory

Hybrid Vector-Graph Memory System for OpenClaw autonomous agents.

## What It Does

Replaces flat markdown memory files with a proper memory system:

- **Vector search** — Semantic similarity via sentence-transformers (all-MiniLM-L6-v2, 384-dim, runs locally)
- **Knowledge graph** — Auto-extracted entities linked via SQLite edges table
- **Hybrid scoring** — Combines cosine similarity (50%), importance (30%), and recency decay (20%)
- **Memory lifecycle** — Episodic → Semantic promotion, staleness decay, duplicate detection

## Quick Start

```bash
pip3 install -r skills/agent-memory/requirements.txt
python3 skills/agent-memory/scripts/memory.py remember "Alice is the lead on Project Atlas"
python3 skills/agent-memory/scripts/memory.py recall "who leads Project Atlas"
python3 skills/agent-memory/scripts/memory.py stats
```

## Commands

| Command | Description |
|---------|-------------|
| `remember <text>` | Store with auto-embedding and entity extraction |
| `recall <query>` | Hybrid vector + graph search |
| `forget <id>` | Soft-delete (decay) |
| `relate <src> <tgt>` | Create explicit graph edge |
| `reflect` | Maintenance: prune stale, find duplicates, promote |
| `timeline` | Chronological retrieval with filters |
| `stats` | Health report (instant, no model loading) |
| `import-md <file>` | Ingest existing markdown files |
| `export` | Dump all memories as JSON |

## Requirements

- Python 3.9+
- macOS ARM / Linux
- ~80MB disk for the embedding model (downloaded on first use)
- No cloud services, no Docker

## Architecture

```
Working Memory (OpenClaw context window)
        ↓ remember
Episodic Memory (timestamped events)
        ↓ reflect (auto-promote)
Semantic Memory (distilled facts + knowledge graph)
```

Storage: SQLite with WAL mode at `memory/agent_memory.db`.

See `SKILL.md` for the full agent-facing manual.
