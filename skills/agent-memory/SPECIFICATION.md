# SPECIFICATION.md — Agent Memory Evolution
*Generated: 2026-02-12 | Confidence: High (full code review + live testing)*

## Objective

Fix the DB path bug, remove test data, integrate with the existing memory workflow (daily markdown files + MEMORY.md), and make this the default recall backend. The code is well-built — this is a configuration+integration pass, not a rewrite.

## Current State

### What Works Well
- Full vector search with sentence-transformers (all-MiniLM-L6-v2)
- Hybrid scoring: cosine sim (0.5) + importance (0.3) + recency (0.2)
- Knowledge graph with auto-linking on entity + similarity overlap
- Keyword fallback when model unavailable
- reflect maintenance cycle (prune, dedup, promote, orphan cleanup)
- Clean CLI with structured JSON output
- 1,194 LOC Python, well-documented

### Problems Found

1. **DB path resolves to `skills/memory/` not `memory/`** — The path computation in utils.py walks up 2 levels from scripts/ (reaching skills/agent-memory/) then joins "memory", landing at `skills/memory/`. Should resolve to workspace `memory/agent_memory.db`.

2. **Test data in DB** — 3 fake memories about Alice/Bob/GraphQL from usage_example or manual testing. Should be cleared.

3. **`skills/memory/` directory exists as false skill** — Created by the DB path bug. Should be cleaned up.

4. **`skillrun` quoting issue** — Multi-word arguments break when passed through the shell wrapper because `run_monitored.py` joins command parts with spaces. Need to handle this.

5. **`import numpy` at top of memory.py** — Hard dependency loaded even for `--help`. Should be lazy like sentence-transformers.

6. **No requirements.txt** — SKILL.md mentions it but file doesn't exist.

7. **Not integrated into workflow** — The agent (me) doesn't use this for recall. Should be wired into heartbeat for periodic import of daily notes.

## Tasks

- [ ] T1: Fix DB path to resolve to `memory/agent_memory.db`
- [ ] T2: Clear test data, remove `skills/memory/` directory
- [ ] T3: Make numpy import lazy (only when embedding operations needed)
- [ ] T4: Create requirements.txt
- [ ] T5: Import existing memory files into the vector store
- [ ] T6: Update HEARTBEAT.md with memory maintenance
