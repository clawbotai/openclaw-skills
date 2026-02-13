---
name: agent-memory
description: Shared brain for all skills — SQLite vector DB with episodic, semantic, and procedural memory. Store, search, and recall context across sessions.
---

# agent-memory — Hybrid Vector-Graph Memory System

## Why This Exists

Agents wake up blank every session. The context window is a goldfish bowl — everything outside it might as well not exist. The traditional workaround is flat markdown files (`MEMORY.md`, daily notes), but these don't scale. Searching them is keyword grep at best, which misses semantic connections ("the API redesign meeting" won't match a note about "GraphQL migration decision"). And as files grow, you spend more tokens loading context than doing useful work.

This skill replaces grep-and-pray with **semantic vector search** and a **lightweight knowledge graph**, both running locally in SQLite. Store a memory once, find it later by meaning — not by remembering which file you put it in or what exact words you used. The knowledge graph connects related memories automatically, so recalling one surfaces its neighbors. No cloud services, no Docker, no external dependencies beyond a one-time model download.

---

## Memory Architecture

Memory flows through three tiers, from volatile to permanent:

### Working Memory (Context Window)

What you're currently thinking about. Managed by the platform, not this skill. Evaporates when the session ends. The entire point of the other two tiers is to rescue valuable information before this happens.

### Episodic Memory (Events)

Timestamped records of things that happened. "Met with Alice on Feb 10 about the API redesign." "User configured Cloudflare Workers for the first time." "Deployment failed because of Python 3.9 compatibility." These are raw, specific, and anchored in time.

Episodic memories are the default storage tier. Most things you `remember` are episodic.

### Semantic Memory (Knowledge)

Distilled facts and patterns extracted from repeated episodes. "Alice is the API team lead." "This workspace uses Python 3.9 — avoid walrus operators and `X | None` syntax." "The user prefers direct answers without hedging."

Semantic memories are promoted from episodic through the `reflect` cycle (automatic) or stored directly when you recognize a durable fact.

### The Flow

```
Conversation happens (Working)
  → You store what matters (remember → Episodic)
    → reflect cycle detects patterns and promotes (Episodic → Semantic)
      → Semantic memories persist indefinitely, episodic ones decay
```

**Real example:**
1. User mentions they hate verbose explanations (Working)
2. You store: "User prefers concise responses, got frustrated with long explanation of git rebase" (→ Episodic)
3. After 5+ similar episodes, reflect promotes: "User communication preference: direct and concise. Skip preambles." (→ Semantic)

### What Goes Where

| Content | Tier | Example |
|---------|------|---------|
| A specific event or conversation | Episodic | "Deployed torr-statics v2.3 on Feb 11" |
| A durable fact about a person/project | Semantic | "Alice leads API team, prefers GraphQL" |
| A user preference observed multiple times | Semantic | "User wants bullet lists, not paragraphs" |
| Today's work log | Daily notes file | "Fixed 3 bugs, reviewed PR #42" |
| A one-off observation | Episodic | "Build broke because Node 25 changed ESM resolution" |
| A lesson learned | Semantic | "Always pin Node version in CI" |

**Rule of thumb:** If you'd tell a replacement agent this fact on day one, it's semantic. If you'd only mention it when asked "what happened last Tuesday," it's episodic. If it's just a log entry, it stays in daily notes and gets indexed via `import-md` later.

---

## Setup

```bash
pip3 install -r skills/agent-memory/requirements.txt
```

First run downloads the embedding model (~80MB, one-time). All subsequent calls use the cached local model.

---

## Commands

All commands output structured JSON. Run from workspace root:

```bash
python3 skills/agent-memory/scripts/memory.py <command> [args]
```

### remember — Store a Memory

```bash
python3 skills/agent-memory/scripts/memory.py remember "Met with Alice about the API redesign. Decided to use GraphQL."
```

Internally: text → 384-dim vector embedding → entity extraction (Alice, API, GraphQL) → importance scoring → auto-linking to related memories via cosine similarity + entity overlap.

Options: `--importance 0.9` (override auto-score, 0.0–1.0), `--type semantic` (default: episodic).

### recall — Search Memories

```bash
python3 skills/agent-memory/scripts/memory.py recall "API redesign decisions"
```

Scoring: `0.5×CosineSimilarity + 0.3×Importance + 0.2×RecencyDecay`. High-scoring results (>0.85) trigger **graph expansion** — linked neighbors are returned with `"via_graph": true`.

Options: `--limit 10` (default: 7).

Falls back to keyword search (SQL LIKE) if the embedding model is unavailable.

### forget — Soft-Delete

```bash
python3 skills/agent-memory/scripts/memory.py forget <memory-id>
```

Marks as decayed. Never physically deletes. Excluded from all searches.

### relate — Link Memories

```bash
python3 skills/agent-memory/scripts/memory.py relate <source-id> <target-id> --relation "contradicts" --weight 0.8
```

Creates an explicit graph edge. Relation types: `relates_to` (default), `contradicts`, `supersedes`, `caused_by`, `part_of`, or any custom string.

### reflect — Maintenance Cycle

```bash
python3 skills/agent-memory/scripts/memory.py reflect
```

Run periodically (1-2x/week via heartbeat or cron). Actions:
1. **Prunes** low-importance memories not accessed in 30+ days
2. **Detects near-duplicates** (cosine similarity >0.95) and suggests merges
3. **Promotes** frequently-accessed episodic memories to semantic (access_count ≥5, importance ≥0.5)
4. **Cleans orphan edges** pointing to decayed memories

Options: `--prune-days 60`, `--similarity-threshold 0.90`.

### timeline — Chronological View

```bash
python3 skills/agent-memory/scripts/memory.py timeline --entity "Alice" --since "2026-01-01"
```

### stats — Health Report

```bash
python3 skills/agent-memory/scripts/memory.py stats
```

Instant (no model loading). Total/active/decayed counts, episodic vs semantic split, importance distribution, staleness, DB size.

### import-md — Ingest Markdown Files

```bash
python3 skills/agent-memory/scripts/memory.py import-md memory/MEMORY.md --type semantic
python3 skills/agent-memory/scripts/memory.py import-md memory/2026-02-11.md --type episodic
```

Splits by headings/paragraphs, embeds each chunk, stores with auto-importance. Use for cold-start migration from existing files.

### export — Dump Everything

```bash
python3 skills/agent-memory/scripts/memory.py export
```

Full JSON export of all active memories and edges (without embeddings).

---

## When Memory Fails — Anti-Patterns

### The Hoarder

**Pattern:** Storing every conversational exchange, debug output, and passing observation. Memory fills with noise.

**Reality:** When everything is important, nothing is. Recall results get diluted by low-value entries. The reflect cycle spends all its time pruning garbage instead of finding patterns. Storage grows linearly while signal-to-noise drops.

**Fix:** Before calling `remember`, ask: "Would a replacement agent need this?" If no, skip it. Reserve memory for decisions, preferences, facts, and lessons — not for "user said hello" or "pip install succeeded."

### The Amnesiac

**Pattern:** Never calling `remember` during conversations. Relying entirely on daily notes and periodic `import-md`.

**Reality:** Daily notes capture what happened but not why. By the time `import-md` runs, the context that made a decision meaningful is gone. The embeddings capture words but miss intent.

**Fix:** Store memories in real-time when they happen. The conversation is still in working memory — that's when you have the richest context to write a meaningful memory entry. `import-md` is a backup, not the primary path.

### The Phantom Memory

**Pattern:** Recalling a "memory" that was never stored — confusing training data knowledge with actual episodic memory.

**Reality:** This is the memory equivalent of hallucination. You "remember" that the user prefers dark mode because that's a common preference in your training data, not because they ever said it. You "recall" a meeting that matches a pattern but never happened.

**Fix:** Trust `recall` results, not your intuition about what you "remember." If `recall` returns nothing, the honest answer is "I don't have that in memory." Never fabricate memory entries to fill gaps. When uncertain, ask the user.

---

## Integration with Existing Files

This system **supplements** `MEMORY.md` and `memory/YYYY-MM-DD.md` files — it does not replace them. Continue writing daily notes as before. The vector store adds searchability on top.

**Recommended workflow:**
1. Write daily notes to `memory/YYYY-MM-DD.md` as usual
2. Use `remember` for important facts during conversation (real-time capture)
3. Run `import-md` on daily files periodically (weekly or via cron)
4. Use `recall` instead of grep for finding past context
5. Run `reflect` during heartbeats to maintain quality

---

## Knowledge Graph

Edges are created automatically when memories share entities and semantic similarity, and explicitly via `relate`. Query the graph indirectly through `recall` (graph expansion) or directly via `export`.

**Entity detection:** Proper nouns (Alice, OpenClaw), acronyms (API, SQL), CamelCase identifiers (GraphQL, SvelteKit).

**Edge types:** `relates_to`, `contradicts`, `supersedes`, `caused_by`, `part_of`, or custom.

---

## Database Details

- **Location:** `memory/agent_memory.db`
- **Engine:** SQLite with WAL mode (concurrent-safe)
- **Tables:** `memories` (content + embedding + metadata), `edges` (knowledge graph)
- **Embedding size:** 1536 bytes per memory (384 × float32)
- **Scaling:** Tested to 100K memories (linear scan). For >100K, consider FAISS indexing.

**Recovery:** Corrupt DB → delete `agent_memory.db` and re-import from markdown files. WAL mode prevents corruption under normal operation. Out of disk → `stats` reports DB size, then `reflect --prune-days 7` to reclaim space.

---

## Integration

- **agent-guardrails**: Log significant guardrail events (denials, injection attempts) as episodic memories for cross-session awareness.
- **agent-orchestration**: Sub-agents have no access to this memory store. Include relevant recalled context in task prompts explicitly.
- **Heartbeat**: Add `reflect` to HEARTBEAT.md for periodic maintenance (1-2x/week).
- **Daily notes**: `import-md` bridges the gap between flat files and vector search.

---

## Quick Reference Card

```
TIERS:    Working (context window) → Episodic (events) → Semantic (facts)
STORE:    remember "text" [--importance N] [--type semantic]
SEARCH:   recall "query" [--limit N]
LINK:     relate <src> <dst> --relation X
MAINTAIN: reflect [--prune-days N]
HISTORY:  timeline --entity "X" --since "YYYY-MM-DD"
HEALTH:   stats
MIGRATE:  import-md <file> --type episodic|semantic
BACKUP:   export

SCORING:  0.5×cosine + 0.3×importance + 0.2×recency
GRAPH:    Auto-links on store. Score>0.85 triggers neighbor expansion.
PROMOTE:  reflect auto-promotes episodic→semantic (access≥5, importance≥0.5)
DECAY:    reflect prunes unaccessed memories after 30 days

python3 skills/agent-memory/scripts/memory.py <command> [args]
```
