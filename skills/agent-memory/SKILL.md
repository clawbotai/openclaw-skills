---
name: agent-memory
description: Shared brain for all skills — SQLite vector DB with episodic, semantic, and procedural memory. Store, search, and recall context across sessions.
---

# agent-memory — Hybrid Vector-Graph Memory System

## What This Is

A 3-tier memory system replacing flat markdown files with **semantic vector search** and a **lightweight knowledge graph**, all running locally in SQLite. No cloud, no Docker, no external services.

**Architecture:**

| Tier | What | Storage | Managed By |
|------|------|---------|------------|
| **Working** | Current conversation context | OpenClaw context window | Platform (not this skill) |
| **Episodic** | Timestamped events, conversations, decisions | `memory/agent_memory.db` | This skill |
| **Semantic** | Distilled facts, relationships, patterns | `memory/agent_memory.db` | This skill (via promotion) |

Memories flow: **Working → Episodic → Semantic** through natural use and reflection cycles.

---

## Setup

```bash
pip3 install -r skills/agent-memory/requirements.txt
```

First run of `remember` or `recall` downloads the embedding model (~80MB, one-time). All subsequent calls use the cached local model.

---

## Commands

All commands output **structured JSON**. Run from workspace root:

```bash
python3 skills/agent-memory/scripts/memory.py <command> [args]
```

### remember — Store a Memory

```bash
python3 skills/agent-memory/scripts/memory.py remember "Met with Alice about the API redesign. Decided to use GraphQL."
```

**What happens internally:**
1. Text is embedded into a 384-dim vector (all-MiniLM-L6-v2)
2. Entities are auto-extracted (Alice, API, GraphQL)
3. Importance is scored heuristically (word count + entity richness)
4. Auto-links to existing related memories via cosine similarity + entity overlap

**Output:**
```json
{
  "status": "stored",
  "id": "a1b2c3d4-...",
  "type": "episodic",
  "importance": 0.65,
  "entities": ["Alice", "API", "GraphQL"],
  "edges_created": 2
}
```

**Options:**
- `--importance 0.9` — Override auto-importance (0.0–1.0)
- `--type semantic` — Store as semantic (default: episodic)

### recall — Search Memories

```bash
python3 skills/agent-memory/scripts/memory.py recall "API redesign decisions"
```

**Scoring formula:**
```
Score = (0.5 × CosineSimilarity) + (0.3 × Importance) + (0.2 × RecencyDecay)
RecencyDecay = 1.0 / (1.0 + log(1 + hours_since_access))
```

High-scoring results (>0.85) trigger **graph expansion** — their linked neighbors are also returned, marked `"via_graph": true`.

**Options:**
- `--limit 10` — Max results (default: 7)

**Fallback:** If the embedding model is unavailable, falls back to keyword search (SQL LIKE) and warns. All results still include scoring.

### forget — Soft-Delete

```bash
python3 skills/agent-memory/scripts/memory.py forget <memory-id>
```

Marks as decayed. Never physically deletes. Excluded from all searches.

### relate — Link Memories

```bash
python3 skills/agent-memory/scripts/memory.py relate <source-id> <target-id> --relation "contradicts" --weight 0.8
```

Creates an explicit graph edge. Used when you notice connections the auto-linker missed.

**Relation types:** `relates_to` (default), `contradicts`, `supersedes`, `caused_by`, `part_of`, or any custom string.

### reflect — Maintenance Cycle

```bash
python3 skills/agent-memory/scripts/memory.py reflect
```

Run this periodically (via heartbeat or cron). It does:

1. **Prunes** low-importance memories not accessed in 30+ days (marks decayed)
2. **Detects near-duplicates** (cosine similarity >0.95) and suggests merges
3. **Promotes** frequently-accessed episodic memories to semantic (access_count ≥5, importance ≥0.5)
4. **Cleans orphan edges** pointing to decayed memories

**Options:**
- `--prune-days 60` — Override staleness threshold (default: 30)
- `--similarity-threshold 0.90` — Override duplicate detection (default: 0.95)

### timeline — Chronological View

```bash
python3 skills/agent-memory/scripts/memory.py timeline --entity "Alice" --since "2026-01-01"
```

Returns memories in reverse chronological order, optionally filtered.

### stats — Health Report

```bash
python3 skills/agent-memory/scripts/memory.py stats
```

Instant (no model loading). Returns: total/active/decayed counts, episodic vs semantic split, importance distribution, staleness, DB size.

### import-md — Ingest Markdown Files

```bash
python3 skills/agent-memory/scripts/memory.py import-md memory/MEMORY.md --type semantic
python3 skills/agent-memory/scripts/memory.py import-md memory/2026-02-11.md --type episodic
```

Splits by headings/paragraphs, embeds each chunk, stores with auto-importance. Use this for cold-start migration from existing files.

### export — Dump Everything

```bash
python3 skills/agent-memory/scripts/memory.py export
```

Full JSON export of all active memories and edges (without embeddings).

---

## When to Use Each Command

| Situation | Command |
|-----------|---------|
| User tells you something worth remembering | `remember` |
| You need context about a person, project, or decision | `recall` |
| You notice two memories are connected | `relate` |
| During heartbeat or scheduled maintenance | `reflect` |
| User asks "what happened with X last month?" | `timeline` |
| Debugging or checking memory health | `stats` |
| First time setup / migrating from markdown | `import-md` |
| Backing up or auditing memory | `export` |

---

## Integration with Existing Memory

This system **supplements** the existing `MEMORY.md` and `memory/YYYY-MM-DD.md` files — it does not replace them. Continue writing daily notes as before. Periodically run `import-md` on new daily files to index them into the vector store.

**Recommended workflow:**
1. Write daily notes to `memory/YYYY-MM-DD.md` as usual
2. Use `remember` for important facts during conversation
3. Run `import-md` on daily files periodically (weekly or via cron)
4. Use `recall` instead of `memory_search` for better results
5. Run `reflect` during heartbeats to maintain quality

---

## Heartbeat Integration

Add to `HEARTBEAT.md`:

```markdown
- [ ] **Memory maintenance** — Run `python3 skills/agent-memory/scripts/memory.py reflect` (1-2x/week)
```

Or schedule via cron for automated maintenance.

---

## Knowledge Graph

The graph is implicit — edges are created automatically when memories share entities and semantic similarity, and explicitly via `relate`. Query the graph indirectly through `recall` (graph expansion) or directly via `export`.

**Entity types detected:** Proper nouns (Alice, OpenClaw), acronyms (API, SQL), CamelCase identifiers (GraphQL, SvelteKit).

**Edge types:** `relates_to`, `contradicts`, `supersedes`, `caused_by`, `part_of`, or custom.

---

## Database

- **Location:** `memory/agent_memory.db`
- **Engine:** SQLite with WAL mode (concurrent-safe)
- **Tables:** `memories` (content + embedding + metadata), `edges` (knowledge graph)
- **Embedding size:** 1536 bytes per memory (384 × float32)
- **Scaling:** Tested to 100K memories. Linear scan is O(n) — for >100K, consider adding FAISS indexing.

---

## Error Handling

- **No internet on first run?** Model download fails → all commands still work via keyword fallback. Install model manually: `python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"`
- **Corrupt DB?** Delete `memory/agent_memory.db` and re-import from markdown files. WAL mode prevents corruption under normal operation.
- **Out of disk?** `stats` reports DB size. `reflect` with aggressive `--prune-days 7` to reclaim space.
