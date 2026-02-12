#!/usr/bin/env python3
"""
agent-memory / memory.py
=========================
Unified CLI entry point for the Hybrid Vector-Graph Memory System.

Subcommands:
    remember <text>                 Store a memory with auto-embedding & entity extraction
    recall <query>                  Hybrid vector + graph search with scored ranking
    forget <id>                     Soft-delete (decay) a memory
    relate <source_id> <target_id>  Create a graph edge between two memories
    reflect                         Maintenance: prune stale memories, find near-duplicates
    timeline [--entity X] [--since] Temporal retrieval of memories
    stats                           Memory system health report
    import-md <file>                Import a markdown file (MEMORY.md or daily notes)
    export                          Dump all memories as JSON

All output is structured JSON for reliable agent consumption.

Usage:
    python3 memory.py remember "Met with Alice about the API redesign project"
    python3 memory.py recall "API redesign"
    python3 memory.py reflect
    python3 memory.py stats
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Local imports — utils handles DB, embeddings, entities
from utils import (
    DEFAULT_DB_PATH,
    blob_to_embedding,
    cosine_similarity,
    embedding_to_blob,
    extract_entities,
    generate_embedding,
    get_connection,
    new_id,
)

import numpy as np


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _json_out(data: Any) -> None:
    """Print a JSON object to stdout and exit cleanly."""
    print(json.dumps(data, indent=2, default=str))


def _error_out(message: str, code: str = "ERROR") -> None:
    """Print a JSON error to stderr and exit with code 1."""
    print(json.dumps({"status": "error", "code": code, "message": message}),
          file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# REMEMBER — store a new memory
# ---------------------------------------------------------------------------

def cmd_remember(args: argparse.Namespace) -> None:
    """Store a new memory with embedding and entity extraction.

    Steps:
      1. Generate embedding via sentence-transformers (or None on failure)
      2. Extract entities via regex heuristics
      3. Assign initial importance (0.5 default, boosted if entities found)
      4. Insert into memories table
      5. Auto-link to existing memories that share extracted entities

    Args:
        args: Parsed CLI args with .text (str), .importance (float|None),
              .type (str), .db (str|None).
    """
    text = args.text
    if not text or not text.strip():
        _error_out("Empty text — nothing to remember.", "EMPTY_INPUT")

    now = time.time()
    mem_id = new_id()
    mem_type = getattr(args, "type", "episodic") or "episodic"

    # Generate embedding (may return None if model unavailable)
    embedding = generate_embedding(text)
    blob = embedding_to_blob(embedding) if embedding is not None else None

    # Extract entities for lightweight knowledge linking
    entities = extract_entities(text)

    # Importance: user-specified, or heuristic based on content richness
    importance = getattr(args, "importance", None)
    if importance is None:
        # Heuristic: longer, entity-rich content is more important
        word_count = len(text.split())
        entity_bonus = min(len(entities) * 0.05, 0.2)
        length_bonus = min(word_count / 100.0, 0.2)
        importance = round(min(0.5 + entity_bonus + length_bonus, 1.0), 3)

    conn = get_connection(args.db)
    try:
        conn.execute(
            """INSERT INTO memories
               (id, content, embedding, created_at, last_accessed,
                access_count, importance, type, decayed)
               VALUES (?, ?, ?, ?, ?, 0, ?, ?, 0)""",
            (mem_id, text.strip(), blob, now, now, importance, mem_type),
        )

        # Auto-link: find existing memories containing the same entities
        edges_created = 0
        if entities and embedding is not None:
            edges_created = _auto_link(conn, mem_id, embedding, entities, now)

        conn.commit()

        _json_out({
            "status": "stored",
            "id": mem_id,
            "type": mem_type,
            "importance": importance,
            "entities": entities,
            "edges_created": edges_created,
        })
    finally:
        conn.close()


def _auto_link(
    conn,
    mem_id: str,
    embedding: np.ndarray,
    entities: List[str],
    now: float,
    similarity_threshold: float = 0.7,
    max_links: int = 5,
) -> int:
    """Create graph edges to existing memories with high semantic similarity.

    Only links memories that are both semantically similar (cosine > threshold)
    AND share at least one extracted entity.  This prevents spurious edges
    from generic topical overlap.

    Args:
        conn: SQLite connection.
        mem_id: ID of the newly created memory.
        embedding: Embedding vector of the new memory.
        entities: Extracted entities from the new memory.
        now: Current timestamp.
        similarity_threshold: Minimum cosine similarity for auto-linking.
        max_links: Maximum number of edges to create.

    Returns:
        Number of edges created.
    """
    # Fetch recent non-decayed memories that have embeddings
    rows = conn.execute(
        """SELECT id, content, embedding FROM memories
           WHERE id != ? AND decayed = 0 AND embedding IS NOT NULL
           ORDER BY last_accessed DESC LIMIT 200""",
        (mem_id,),
    ).fetchall()

    candidates = []  # type: List[Tuple[str, float]]
    entity_lower = {e.lower() for e in entities}

    for row in rows:
        other_emb = blob_to_embedding(row["embedding"])
        sim = cosine_similarity(embedding, other_emb)
        if sim < similarity_threshold:
            continue
        # Check entity overlap
        other_entities = {e.lower() for e in extract_entities(row["content"])}
        if entity_lower & other_entities:
            candidates.append((row["id"], sim))

    # Sort by similarity descending, take top N
    candidates.sort(key=lambda x: x[1], reverse=True)
    count = 0
    for target_id, sim in candidates[:max_links]:
        conn.execute(
            """INSERT INTO edges (id, source, target, relation, weight, created_at)
               VALUES (?, ?, ?, 'relates_to', ?, ?)""",
            (new_id(), mem_id, target_id, round(sim, 4), now),
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# RECALL — hybrid vector + graph search
# ---------------------------------------------------------------------------

def cmd_recall(args: argparse.Namespace) -> None:
    """Retrieve memories using hybrid scoring: vector similarity + importance + recency.

    Scoring formula:
        Score = (0.5 × CosineSimilarity) + (0.3 × Importance) + (0.2 × RecencyDecay)
        RecencyDecay = 1.0 / (1.0 + log(1 + hours_since_access))

    High-scoring memories (>0.85) trigger graph expansion: their directly
    connected neighbors are also returned (deduplicated, marked as "via_graph").

    Falls back to SQL LIKE keyword search if embeddings are unavailable.

    Args:
        args: Parsed CLI args with .query (str), .limit (int), .db (str|None).
    """
    query = args.query
    if not query or not query.strip():
        _error_out("Empty query.", "EMPTY_QUERY")

    limit = getattr(args, "limit", 7) or 7
    conn = get_connection(args.db)
    now = time.time()

    try:
        query_embedding = generate_embedding(query)

        if query_embedding is not None:
            results = _vector_recall(conn, query_embedding, now, limit)
        else:
            # Fallback: keyword search
            results = _keyword_recall(conn, query, now, limit)

        # Graph expansion for high-confidence results
        expanded = []  # type: List[Dict]
        seen_ids = {r["id"] for r in results}

        for r in results:
            if r["score"] > 0.85:
                neighbors = _graph_neighbors(conn, r["id"], now)
                for n in neighbors:
                    if n["id"] not in seen_ids:
                        n["via_graph"] = True
                        n["linked_from"] = r["id"]
                        expanded.append(n)
                        seen_ids.add(n["id"])

        # Update access timestamps for returned memories
        all_ids = [r["id"] for r in results + expanded]
        if all_ids:
            placeholders = ",".join("?" * len(all_ids))
            conn.execute(
                f"""UPDATE memories
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE id IN ({placeholders})""",
                [now] + all_ids,
            )
            conn.commit()

        _json_out({
            "status": "ok",
            "query": query,
            "count": len(results) + len(expanded),
            "results": results + expanded[:3],  # cap graph expansion at 3
            "search_mode": "vector" if query_embedding is not None else "keyword",
        })
    finally:
        conn.close()


def _vector_recall(
    conn, query_vec: np.ndarray, now: float, limit: int
) -> List[Dict]:
    """Score all non-decayed memories against the query vector.

    Loads embeddings from SQLite and computes the hybrid score in Python.
    This is O(n) over all memories — acceptable for <100K memories on local
    hardware.  For larger stores, consider sqlite-vss or FAISS indexing.

    Args:
        conn: SQLite connection.
        query_vec: The query's embedding vector.
        now: Current timestamp for recency calculation.
        limit: Max results to return.

    Returns:
        List of scored memory dicts, sorted by score descending.
    """
    rows = conn.execute(
        """SELECT id, content, embedding, created_at, last_accessed,
                  access_count, importance, type
           FROM memories WHERE decayed = 0 AND embedding IS NOT NULL"""
    ).fetchall()

    scored = []  # type: List[Tuple[float, Dict]]
    for row in rows:
        emb = blob_to_embedding(row["embedding"])
        sim = cosine_similarity(query_vec, emb)

        hours_since = max((now - row["last_accessed"]) / 3600.0, 0.0)
        recency = 1.0 / (1.0 + math.log(1.0 + hours_since))

        score = (0.5 * sim) + (0.3 * row["importance"]) + (0.2 * recency)

        scored.append((score, {
            "id": row["id"],
            "content": row["content"],
            "type": row["type"],
            "importance": row["importance"],
            "score": round(score, 4),
            "cosine_similarity": round(sim, 4),
            "recency_decay": round(recency, 4),
            "created_at": row["created_at"],
            "last_accessed": row["last_accessed"],
            "access_count": row["access_count"],
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def _keyword_recall(
    conn, query: str, now: float, limit: int
) -> List[Dict]:
    """Fallback search using SQL LIKE when embeddings are unavailable.

    Splits the query into words and matches any memory containing all words
    (case-insensitive).  Scored by importance and recency only.

    Args:
        conn: SQLite connection.
        query: Search query string.
        now: Current timestamp.
        limit: Max results.

    Returns:
        List of scored memory dicts.
    """
    words = [w.strip() for w in query.split() if len(w.strip()) >= 2]
    if not words:
        return []

    # Build WHERE clause: content LIKE '%word1%' AND content LIKE '%word2%' ...
    conditions = " AND ".join(["content LIKE ?"] * len(words))
    params = [f"%{w}%" for w in words]

    rows = conn.execute(
        f"""SELECT id, content, created_at, last_accessed,
                   access_count, importance, type
            FROM memories
            WHERE decayed = 0 AND ({conditions})
            ORDER BY importance DESC, last_accessed DESC
            LIMIT ?""",
        params + [limit],
    ).fetchall()

    results = []  # type: List[Dict]
    for row in rows:
        hours_since = max((now - row["last_accessed"]) / 3600.0, 0.0)
        recency = 1.0 / (1.0 + math.log(1.0 + hours_since))
        score = (0.3 * row["importance"]) + (0.2 * recency) + 0.5  # no sim

        results.append({
            "id": row["id"],
            "content": row["content"],
            "type": row["type"],
            "importance": row["importance"],
            "score": round(score, 4),
            "cosine_similarity": None,
            "recency_decay": round(recency, 4),
            "created_at": row["created_at"],
            "last_accessed": row["last_accessed"],
            "access_count": row["access_count"],
        })
    return results


def _graph_neighbors(conn, mem_id: str, now: float) -> List[Dict]:
    """Fetch directly connected memories via the edges table.

    Returns neighbors sorted by edge weight descending.

    Args:
        conn: SQLite connection.
        mem_id: Memory ID to expand from.
        now: Current timestamp.

    Returns:
        List of neighbor memory dicts with edge metadata.
    """
    rows = conn.execute(
        """SELECT m.id, m.content, m.importance, m.type,
                  m.created_at, m.last_accessed, m.access_count,
                  e.relation, e.weight
           FROM edges e
           JOIN memories m ON (
               (e.source = ? AND m.id = e.target) OR
               (e.target = ? AND m.id = e.source)
           )
           WHERE m.decayed = 0
           ORDER BY e.weight DESC
           LIMIT 5""",
        (mem_id, mem_id),
    ).fetchall()

    results = []  # type: List[Dict]
    for row in rows:
        hours_since = max((now - row["last_accessed"]) / 3600.0, 0.0)
        recency = 1.0 / (1.0 + math.log(1.0 + hours_since))

        results.append({
            "id": row["id"],
            "content": row["content"],
            "type": row["type"],
            "importance": row["importance"],
            "score": round(0.3 * row["importance"] + 0.2 * recency + 0.5 * row["weight"], 4),
            "edge_relation": row["relation"],
            "edge_weight": row["weight"],
            "created_at": row["created_at"],
            "last_accessed": row["last_accessed"],
            "access_count": row["access_count"],
        })
    return results


# ---------------------------------------------------------------------------
# FORGET — soft-delete a memory
# ---------------------------------------------------------------------------

def cmd_forget(args: argparse.Namespace) -> None:
    """Mark a memory as decayed (soft-delete).

    Decayed memories are excluded from recall but never physically deleted.
    They can be restored by setting decayed=0.

    Args:
        args: Parsed CLI args with .id (str).
    """
    conn = get_connection(args.db)
    try:
        cur = conn.execute(
            "UPDATE memories SET decayed = 1 WHERE id = ?", (args.id,)
        )
        conn.commit()
        if cur.rowcount == 0:
            _error_out(f"Memory {args.id} not found.", "NOT_FOUND")
        _json_out({"status": "decayed", "id": args.id})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# RELATE — create a graph edge
# ---------------------------------------------------------------------------

def cmd_relate(args: argparse.Namespace) -> None:
    """Create an explicit edge between two memories in the knowledge graph.

    Args:
        args: Parsed CLI args with .source (str), .target (str),
              .relation (str), .weight (float).
    """
    conn = get_connection(args.db)
    now = time.time()
    try:
        # Verify both memories exist
        for mid in (args.source, args.target):
            row = conn.execute(
                "SELECT id FROM memories WHERE id = ?", (mid,)
            ).fetchone()
            if not row:
                _error_out(f"Memory {mid} not found.", "NOT_FOUND")

        edge_id = new_id()
        relation = getattr(args, "relation", "relates_to") or "relates_to"
        weight = getattr(args, "weight", 1.0) or 1.0

        conn.execute(
            """INSERT INTO edges (id, source, target, relation, weight, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (edge_id, args.source, args.target, relation, weight, now),
        )
        conn.commit()
        _json_out({
            "status": "linked",
            "edge_id": edge_id,
            "source": args.source,
            "target": args.target,
            "relation": relation,
            "weight": weight,
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# REFLECT — maintenance cycle
# ---------------------------------------------------------------------------

def cmd_reflect(args: argparse.Namespace) -> None:
    """Run memory maintenance: prune stale memories and detect near-duplicates.

    Pruning:
        Memories with importance < 0.2 AND last_accessed > 30 days ago
        are marked as decayed.

    Clustering:
        All non-decayed memory pairs are checked for cosine similarity > 0.95.
        Near-duplicates are reported as merge candidates (not auto-merged,
        to preserve agent oversight).

    Args:
        args: Parsed CLI args with .db (str|None), .prune_days (int),
              .similarity_threshold (float).
    """
    conn = get_connection(args.db)
    now = time.time()
    prune_days = getattr(args, "prune_days", 30) or 30
    sim_threshold = getattr(args, "similarity_threshold", 0.95) or 0.95

    try:
        # --- Phase 1: Prune stale low-importance memories ---
        cutoff = now - (prune_days * 86400)
        cur = conn.execute(
            """UPDATE memories SET decayed = 1
               WHERE importance < 0.2
                 AND last_accessed < ?
                 AND decayed = 0""",
            (cutoff,),
        )
        pruned_count = cur.rowcount

        # --- Phase 2: Find near-duplicate clusters ---
        rows = conn.execute(
            """SELECT id, content, embedding FROM memories
               WHERE decayed = 0 AND embedding IS NOT NULL"""
        ).fetchall()

        duplicates = []  # type: List[Dict]
        embeddings = []  # type: List[Tuple[str, str, np.ndarray]]
        for row in rows:
            embeddings.append((
                row["id"], row["content"], blob_to_embedding(row["embedding"])
            ))

        # O(n²) comparison — acceptable for <10K memories.
        # For larger stores, use approximate nearest neighbors.
        checked = set()  # type: set
        for i, (id_a, content_a, emb_a) in enumerate(embeddings):
            for j in range(i + 1, len(embeddings)):
                id_b, content_b, emb_b = embeddings[j]
                pair_key = (id_a, id_b) if id_a < id_b else (id_b, id_a)
                if pair_key in checked:
                    continue
                checked.add(pair_key)

                sim = cosine_similarity(emb_a, emb_b)
                if sim >= sim_threshold:
                    duplicates.append({
                        "memory_a": {"id": id_a, "content": content_a[:120]},
                        "memory_b": {"id": id_b, "content": content_b[:120]},
                        "similarity": round(sim, 4),
                        "suggestion": "merge",
                    })

        # --- Phase 3: Promote frequently-accessed episodic → semantic ---
        promoted = conn.execute(
            """UPDATE memories SET type = 'semantic'
               WHERE type = 'episodic'
                 AND access_count >= 5
                 AND importance >= 0.5
                 AND decayed = 0"""
        ).rowcount

        # --- Phase 4: Orphan edge cleanup ---
        orphan_edges = conn.execute(
            """DELETE FROM edges
               WHERE source IN (SELECT id FROM memories WHERE decayed = 1)
                  OR target IN (SELECT id FROM memories WHERE decayed = 1)"""
        ).rowcount

        conn.commit()

        _json_out({
            "status": "ok",
            "pruned": pruned_count,
            "near_duplicates": duplicates,
            "duplicate_count": len(duplicates),
            "promoted_to_semantic": promoted,
            "orphan_edges_removed": orphan_edges,
            "total_active": conn.execute(
                "SELECT COUNT(*) FROM memories WHERE decayed = 0"
            ).fetchone()[0],
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# TIMELINE — temporal retrieval
# ---------------------------------------------------------------------------

def cmd_timeline(args: argparse.Namespace) -> None:
    """Retrieve memories in chronological order, optionally filtered by entity.

    Args:
        args: Parsed CLI args with .entity (str|None), .since (str|None),
              .limit (int).
    """
    conn = get_connection(args.db)
    limit = getattr(args, "limit", 20) or 20

    try:
        conditions = ["decayed = 0"]
        params = []  # type: List[Any]

        entity = getattr(args, "entity", None)
        if entity:
            conditions.append("content LIKE ?")
            params.append(f"%{entity}%")

        since = getattr(args, "since", None)
        if since:
            # Parse ISO date string to timestamp
            import datetime
            try:
                dt = datetime.datetime.fromisoformat(since)
                conditions.append("created_at >= ?")
                params.append(dt.timestamp())
            except ValueError:
                _error_out(f"Invalid date format: {since}. Use ISO 8601.", "BAD_DATE")

        where = " AND ".join(conditions)
        params.append(limit)

        rows = conn.execute(
            f"""SELECT id, content, type, importance, created_at,
                       last_accessed, access_count
                FROM memories
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?""",
            params,
        ).fetchall()

        results = [dict(row) for row in rows]
        _json_out({
            "status": "ok",
            "count": len(results),
            "timeline": results,
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# STATS — health report
# ---------------------------------------------------------------------------

def cmd_stats(args: argparse.Namespace) -> None:
    """Report memory system health statistics.

    No embeddings loaded — this command is instant.
    """
    conn = get_connection(args.db)
    try:
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE decayed = 0"
        ).fetchone()[0]
        decayed = total - active
        episodic = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE type = 'episodic' AND decayed = 0"
        ).fetchone()[0]
        semantic = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE type = 'semantic' AND decayed = 0"
        ).fetchone()[0]
        edges_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

        # Importance distribution
        imp_high = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE importance >= 0.7 AND decayed = 0"
        ).fetchone()[0]
        imp_med = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE importance >= 0.3 AND importance < 0.7 AND decayed = 0"
        ).fetchone()[0]
        imp_low = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE importance < 0.3 AND decayed = 0"
        ).fetchone()[0]

        # Staleness: memories not accessed in 7+ days
        week_ago = time.time() - (7 * 86400)
        stale = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE last_accessed < ? AND decayed = 0",
            (week_ago,),
        ).fetchone()[0]

        # DB file size
        db_path = args.db or DEFAULT_DB_PATH
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        _json_out({
            "status": "ok",
            "total_memories": total,
            "active": active,
            "decayed": decayed,
            "episodic": episodic,
            "semantic": semantic,
            "edges": edges_count,
            "importance_distribution": {
                "high_gte_0.7": imp_high,
                "medium_0.3_0.7": imp_med,
                "low_lt_0.3": imp_low,
            },
            "stale_7d": stale,
            "db_size_bytes": db_size,
            "db_size_human": _human_size(db_size),
            "db_path": db_path,
        })
    finally:
        conn.close()


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore
    return f"{size_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# IMPORT-MD — ingest existing markdown memory files
# ---------------------------------------------------------------------------

def cmd_import_md(args: argparse.Namespace) -> None:
    """Import a markdown file into the memory store.

    Splits the file by headings (## or ###) or double-newlines into chunks,
    then stores each chunk as a separate memory.  Useful for cold-starting
    the memory system from existing MEMORY.md or daily note files.

    Args:
        args: Parsed CLI args with .file (str), .type (str).
    """
    import re as re_mod

    filepath = args.file
    if not os.path.exists(filepath):
        _error_out(f"File not found: {filepath}", "FILE_NOT_FOUND")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by markdown headings or double-newlines
    chunks = re_mod.split(r"\n(?=##\s|\n\n)", content)
    chunks = [c.strip() for c in chunks if c.strip() and len(c.strip()) > 20]

    if not chunks:
        _error_out("No meaningful content found to import.", "EMPTY_FILE")

    conn = get_connection(args.db)
    now = time.time()
    mem_type = getattr(args, "type", "semantic") or "semantic"
    imported = 0

    try:
        for chunk in chunks:
            mem_id = new_id()
            embedding = generate_embedding(chunk)
            blob = embedding_to_blob(embedding) if embedding is not None else None
            entities = extract_entities(chunk)

            word_count = len(chunk.split())
            entity_bonus = min(len(entities) * 0.05, 0.2)
            length_bonus = min(word_count / 100.0, 0.2)
            importance = round(min(0.5 + entity_bonus + length_bonus, 1.0), 3)

            conn.execute(
                """INSERT INTO memories
                   (id, content, embedding, created_at, last_accessed,
                    access_count, importance, type, decayed)
                   VALUES (?, ?, ?, ?, ?, 0, ?, ?, 0)""",
                (mem_id, chunk, blob, now, now, importance, mem_type),
            )
            imported += 1

        conn.commit()
        _json_out({
            "status": "imported",
            "file": filepath,
            "chunks_imported": imported,
            "type": mem_type,
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# EXPORT — dump all memories as JSON
# ---------------------------------------------------------------------------

def cmd_export(args: argparse.Namespace) -> None:
    """Export all active memories as a JSON array (without embeddings)."""
    conn = get_connection(args.db)
    try:
        rows = conn.execute(
            """SELECT id, content, created_at, last_accessed,
                      access_count, importance, type
               FROM memories WHERE decayed = 0
               ORDER BY created_at DESC"""
        ).fetchall()

        edges = conn.execute(
            """SELECT source, target, relation, weight, created_at
               FROM edges"""
        ).fetchall()

        _json_out({
            "status": "ok",
            "memories": [dict(r) for r in rows],
            "edges": [dict(e) for e in edges],
            "total_memories": len(rows),
            "total_edges": len(edges),
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI for all memory subcommands."""
    parser = argparse.ArgumentParser(
        prog="memory.py",
        description="Hybrid Vector-Graph Memory System for OpenClaw agents.",
    )
    parser.add_argument(
        "--db", default=None,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    # remember
    p_rem = subs.add_parser("remember", help="Store a new memory")
    p_rem.add_argument("text", help="Text to remember")
    p_rem.add_argument("--importance", type=float, default=None,
                       help="Override importance (0.0-1.0)")
    p_rem.add_argument("--type", choices=["episodic", "semantic"],
                       default="episodic", help="Memory type")

    # recall
    p_rec = subs.add_parser("recall", help="Search memories")
    p_rec.add_argument("query", help="Search query")
    p_rec.add_argument("--limit", type=int, default=7,
                       help="Max results (default: 7)")

    # forget
    p_fg = subs.add_parser("forget", help="Soft-delete a memory")
    p_fg.add_argument("id", help="Memory ID to decay")

    # relate
    p_rel = subs.add_parser("relate", help="Link two memories")
    p_rel.add_argument("source", help="Source memory ID")
    p_rel.add_argument("target", help="Target memory ID")
    p_rel.add_argument("--relation", default="relates_to",
                       help="Edge label (default: relates_to)")
    p_rel.add_argument("--weight", type=float, default=1.0,
                       help="Edge weight (default: 1.0)")

    # reflect
    p_ref = subs.add_parser("reflect", help="Run maintenance cycle")
    p_ref.add_argument("--prune-days", type=int, default=30,
                       help="Prune memories older than N days (default: 30)")
    p_ref.add_argument("--similarity-threshold", type=float, default=0.95,
                       help="Near-duplicate threshold (default: 0.95)")

    # timeline
    p_tl = subs.add_parser("timeline", help="Chronological memory retrieval")
    p_tl.add_argument("--entity", default=None,
                      help="Filter by entity/keyword")
    p_tl.add_argument("--since", default=None,
                      help="ISO 8601 date cutoff")
    p_tl.add_argument("--limit", type=int, default=20,
                      help="Max results (default: 20)")

    # stats
    subs.add_parser("stats", help="Memory system health report")

    # import-md
    p_imp = subs.add_parser("import-md", help="Import a markdown file")
    p_imp.add_argument("file", help="Path to markdown file")
    p_imp.add_argument("--type", choices=["episodic", "semantic"],
                       default="semantic", help="Memory type for imports")

    # export
    subs.add_parser("export", help="Export all memories as JSON")

    return parser


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

# Need os for stats db_size check
import os

_DISPATCH = {
    "remember": cmd_remember,
    "recall": cmd_recall,
    "forget": cmd_forget,
    "relate": cmd_relate,
    "reflect": cmd_reflect,
    "timeline": cmd_timeline,
    "stats": cmd_stats,
    "import-md": cmd_import_md,
    "export": cmd_export,
}

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handler = _DISPATCH.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)
