# Prompt: Design the `agent-memory` Skill for an Autonomous AI Agent

## Context

You are designing a skill called `agent-memory` for **OpenClaw**, an open-source autonomous AI agent platform. OpenClaw agents run locally on macOS/Linux, communicate via messaging surfaces (Signal, Telegram, Discord, WhatsApp, webchat), and use Claude/GPT as their LLM backbone. The agent has access to: filesystem read/write, shell execution, web search, web fetch, browser automation, sub-agent spawning, cron scheduling, and messaging.

**Current memory system (what we're replacing):** Flat markdown files — `MEMORY.md` for long-term curated memory, `memory/YYYY-MM-DD.md` for daily logs. The agent's built-in `memory_search` tool does basic semantic search over these files. There is no embedding storage, no vector database, no knowledge graph, no structured retrieval beyond grep/semantic search over plaintext.

**Why this matters:** The 2025-2026 research consensus (arxiv.org/html/2510.25445v1, McKinsey's agentic AI architecture guide, VLDB's "Towards the Next Generation of Agent Systems") identifies **contextual memory** as one of the 4 defining capabilities of agentic AI alongside planning, tool use, and self-correction. Current flat-file memory fails at: relationship modeling, temporal reasoning, multi-hop retrieval, knowledge decay/freshness, and scales poorly beyond ~100KB of accumulated notes.

## Platform Constraints

- **Runtime:** Python 3.9 on macOS ARM (Apple Silicon), no Docker required
- **Dependencies:** Must be pip-installable. Prefer lightweight libs. No cloud services required (must work fully offline).
- **Storage:** Local filesystem only. SQLite is acceptable. No external vector DBs (no Pinecone, Weaviate, Chroma cloud). An embedded solution like `chromadb` (local mode), `faiss`, or `sqlite-vss` is fine.
- **Credentials:** macOS Keychain only for any API keys. Never plaintext on disk.
- **LLM Access:** The agent calls its LLM through OpenClaw's native tool interface, NOT direct API calls. The skill should provide prompts/templates, not make LLM calls itself.
- **File budget:** SKILL.md should be comprehensive but under 800 lines. Python scripts should be well-commented with docstrings on all functions. Total skill directory < 50KB excluding dependencies.
- **Typing:** Use `typing.Optional[X]` not `X | None` (Python 3.9 compat)

## What to Design

### 1. SKILL.md — The Agent's Instruction Manual
This is what the AI agent reads to know how to use the skill. It should cover:

**Memory Architecture (3-tier):**
- **Working Memory** — Current session context, recent conversation. Already handled by OpenClaw's context window. The skill doesn't need to manage this.
- **Episodic Memory** — Time-stamped events, conversations, decisions. Currently daily markdown files. Upgrade to structured storage with embeddings for semantic retrieval.
- **Semantic Memory** — Distilled facts, relationships, preferences, learned patterns. Currently MEMORY.md. Upgrade to a knowledge store with entity-relationship modeling.

**Core Operations the agent should be able to perform:**
- `remember <text>` — Store a new memory with automatic categorization, entity extraction, and embedding
- `recall <query>` — Semantic search across all memory tiers, ranked by relevance × recency × importance
- `forget <id>` — Mark a memory as decayed/archived (soft delete, never hard delete)
- `reflect` — Periodic consolidation: promote episodic → semantic, merge duplicates, decay stale memories
- `relate <entity_a> <entity_b>` — Explicitly link two entities/concepts
- `timeline <entity_or_topic> [--since DATE]` — Temporal retrieval of everything related to a subject
- `stats` — Memory health: total memories, storage size, staleness distribution, entity count

**Knowledge Graph (lightweight):**
- Entity extraction from conversations (people, projects, tools, decisions, preferences)
- Relationship edges: person→works_on→project, tool→used_for→task, decision→made_on→date
- Don't over-engineer — SQLite with a simple nodes/edges table, not a full graph DB
- Queryable: "What do I know about [person]?" should return all connected facts

**Memory Consolidation (the reflect cycle):**
- Run during heartbeats or scheduled via cron
- Merge near-duplicate memories (cosine similarity > 0.92)
- Promote frequently-accessed episodic memories to semantic
- Decay memories not accessed in 30+ days (reduce retrieval priority, don't delete)
- Generate a "memory health" report

**Backward Compatibility:**
- Must still read/write the existing `memory/YYYY-MM-DD.md` files and `MEMORY.md`
- The structured store supplements but doesn't replace the markdown files
- Agent can use either system; the skill bridges both

### 2. Python Scripts

**`scripts/memory_store.py`** — The core engine:
- SQLite database at `memory/agent_memory.db`
- Tables: `memories` (id, content, category, importance, embedding, created_at, accessed_at, access_count, decayed), `entities` (id, name, type, first_seen, last_seen), `relations` (id, source_entity, target_entity, relation_type, context, created_at)
- Embedding generation: Use `sentence-transformers` with a small local model (e.g., `all-MiniLM-L6-v2`, 80MB) OR if that's too heavy, use a simple TF-IDF approach with scikit-learn. Design it so the embedding backend is swappable.
- CLI interface matching the operations above
- All output as structured JSON for agent consumption

**`scripts/memory_consolidate.py`** — The reflect/maintenance cycle:
- Duplicate detection via embedding similarity
- Importance scoring (access frequency × recency × explicit importance flag)
- Staleness detection and decay
- Entity graph maintenance (merge duplicate entities, prune orphans)
- Outputs a consolidation report as JSON

### 3. Integration Patterns
- How the agent should call these scripts during normal conversation
- How to wire consolidation into HEARTBEAT.md
- How to handle the cold-start problem (importing existing MEMORY.md and daily files)
- Migration path: day 1 the old files still work, day 30 the structured store is primary

## Research References
- Agentic AI survey (arxiv 2510.25445): contextual memory as defining agent capability
- Graphiti (knowledge graph memory for agents): entity-relationship temporal modeling
- VLDB 2025 "Towards Next Gen Agent Systems": episodic + semantic memory tiers
- MemGPT / Letta: hierarchical memory management for LLM agents

## Output Format
Produce:
1. Complete `SKILL.md` (the agent-facing instruction manual)
2. Complete `scripts/memory_store.py` with full implementation
3. Complete `scripts/memory_consolidate.py` with full implementation
4. `_meta.json` for the skill
5. A brief `README.md` for humans

Design for a real production system, not a demo. The agent using this will be running 24/7, accumulating memories over months. It needs to scale gracefully, degrade gracefully when storage fills, and never lose data.
