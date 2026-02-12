# Contributing to agent-memory

## Overview

This skill provides a hybrid vector-graph memory system for AI agents. Memories are embedded with sentence-transformers, stored in SQLite, linked via a lightweight knowledge graph, and retrieved with a hybrid scoring formula.

## File Structure

```
agent-memory/
├── SKILL.md              # Full usage documentation
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # This file
├── requirements.txt      # Python dependencies (sentence-transformers, numpy)
├── _meta.json            # Skill metadata
├── scripts/
│   ├── memory.py         # CLI entry point: remember, recall, forget, relate, reflect, timeline, stats, import-md, export
│   └── utils.py          # Shared utilities: DB connection, embeddings, entity extraction, cosine similarity
```

## Development Setup

```bash
# Install dependencies (downloads ~80 MB embedding model on first run)
pip3 install -r skills/agent-memory/requirements.txt

# Verify installation
python3 skills/agent-memory/scripts/memory.py stats
```

**Dependencies:** `sentence-transformers`, `numpy` (pulled transitively). Python 3.10+.

## Running Tests

No formal test suite yet. Manual verification:

```bash
# Store and recall
python3 skills/agent-memory/scripts/memory.py remember "Test memory about GraphQL migration"
python3 skills/agent-memory/scripts/memory.py recall "GraphQL"

# Maintenance
python3 skills/agent-memory/scripts/memory.py reflect
python3 skills/agent-memory/scripts/memory.py stats

# Import existing markdown
python3 skills/agent-memory/scripts/memory.py import-md memory/MEMORY.md --type semantic

# Export for backup
python3 skills/agent-memory/scripts/memory.py export
```

To add automated tests, create `tests/` with pytest. Key areas to cover:
- Embedding generation and serialization round-trip
- Cosine similarity edge cases (zero vectors, identical vectors)
- Entity extraction patterns (proper nouns, acronyms, CamelCase)
- Recall scoring formula correctness
- Reflection pruning/promotion logic
- Keyword fallback when model is unavailable

## Coding Standards

- **Style:** PEP 8
- **Type hints:** All function signatures annotated; use `from __future__ import annotations`
- **Docstrings:** Google-style with `Args:` and `Returns:` on every function
- **Output:** All CLI commands produce structured JSON to stdout; errors to stderr
- **Imports:** Lazy-load heavy dependencies (sentence-transformers) so lightweight commands (`stats`, `--help`) stay fast

## Making Changes

1. **New subcommand** — Add `cmd_<name>` in `memory.py`, register in `_DISPATCH` and `build_parser()`
2. **Schema changes** — Append new CREATE TABLE/INDEX to `_SCHEMA_SQL` in `utils.py` (SQLite is append-only for migrations)
3. **Scoring changes** — Update the formula in `_vector_recall` and document the new weights in SKILL.md
4. **New entity patterns** — Extend `_ENTITY_RE` in `utils.py`

## PR Process

1. Branch from `main` (`feat/memory-...`, `fix/memory-...`)
2. Ensure JSON output contracts are backward-compatible
3. Update SKILL.md if commands or behavior change
4. Update CHANGELOG.md under `[Unreleased]`
5. Test manually with the commands above
6. Commit with conventional commits (`feat:`, `fix:`, `docs:`)
