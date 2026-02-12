#!/usr/bin/env python3
"""
agent-memory / utils.py
========================
Shared utilities for the Hybrid Vector-Graph Memory System.

Responsibilities:
  - SQLite connection management with WAL mode
  - Schema creation and migration
  - Embedding generation with lazy-loaded sentence-transformers
  - Cosine similarity computation
  - Fallback keyword search when embeddings are unavailable

The embedding model (all-MiniLM-L6-v2) is loaded ONCE per process and
cached in a module-level singleton to avoid repeated 2-3s load times.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import struct
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 384 dimensions for all-MiniLM-L6-v2
EMBEDDING_DIM: int = 384
MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

# Default DB location — resolved relative to the workspace root.
# Script is at: skills/agent-memory/scripts/utils.py
# Workspace is: 3 levels up → skills/agent-memory/scripts → skills/agent-memory → skills → workspace
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_ROOT = os.path.realpath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
_DEFAULT_DB_DIR = os.environ.get(
    "AGENT_MEMORY_DIR",
    os.path.join(_WORKSPACE_ROOT, "memory"),
)
DEFAULT_DB_PATH: str = os.path.join(_DEFAULT_DB_DIR, "agent_memory.db")

logger = logging.getLogger("agent-memory")

# ---------------------------------------------------------------------------
# Embedding model singleton (lazy-loaded)
# ---------------------------------------------------------------------------

_model_instance = None  # type: ignore
_model_load_failed: bool = False


def _get_model():
    """Return the cached SentenceTransformer model, loading it on first call.

    The import is deferred so that CLI commands that don't need embeddings
    (e.g. ``stats``, ``--help``) start instantly.

    Returns:
        SentenceTransformer model instance, or None if loading failed.
    """
    global _model_instance, _model_load_failed
    if _model_instance is not None:
        return _model_instance
    if _model_load_failed:
        return None
    try:
        from sentence_transformers import SentenceTransformer  # lazy import
        _model_instance = SentenceTransformer(MODEL_NAME)
        logger.info("Loaded embedding model: %s", MODEL_NAME)
        return _model_instance
    except Exception as exc:
        _model_load_failed = True
        logger.warning(
            "Failed to load embedding model (%s). "
            "Falling back to keyword search. Error: %s",
            MODEL_NAME, exc,
        )
        return None


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def generate_embedding(text: str) -> Optional[np.ndarray]:
    """Encode *text* into a 384-dim float32 vector.

    Args:
        text: The string to embed.

    Returns:
        numpy float32 array of shape (384,), or None if the model is
        unavailable.
    """
    model = _get_model()
    if model is None:
        return None
    vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return vec.astype(np.float32)


def embedding_to_blob(vec: np.ndarray) -> bytes:
    """Serialize a numpy float32 vector to bytes for SQLite BLOB storage.

    Uses raw float32 little-endian packing — compact (384 × 4 = 1536 bytes)
    and fast to deserialize.
    """
    return vec.astype(np.float32).tobytes()


def blob_to_embedding(blob: bytes) -> np.ndarray:
    """Deserialize a BLOB back to a numpy float32 vector."""
    return np.frombuffer(blob, dtype=np.float32).copy()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Both vectors are assumed to be L2-normalized (sentence-transformers does
    this when ``normalize_embeddings=True``), so the dot product IS the
    cosine similarity.  We still guard against zero vectors.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Entity extraction (lightweight heuristic)
# ---------------------------------------------------------------------------

# Matches capitalized multi-word names, tech terms, etc.
_ENTITY_RE = re.compile(
    r"""
    (?:                         # Option A: Capitalized phrases (2+ words)
        [A-Z][a-z]+             #   First capitalized word
        (?:\s+[A-Z][a-z]+)+    #   Followed by 1+ more capitalized words
    )
    |                           # Option B: ALL-CAPS acronyms (2-6 chars)
    (?:\b[A-Z]{2,6}\b)
    |                           # Option C: CamelCase / PascalCase identifiers
    (?:[A-Z][a-z]+(?:[A-Z][a-z]+)+)
    """,
    re.VERBOSE,
)

# Common stop-words to exclude from entity extraction
_STOP_ENTITIES = frozenset({
    "The", "This", "That", "These", "Those", "There", "Here",
    "What", "When", "Where", "Which", "Who", "How", "Why",
    "AND", "BUT", "FOR", "NOR", "NOT", "YET", "THE",
    "Also", "However", "Therefore", "Furthermore", "Moreover",
})


def extract_entities(text: str) -> List[str]:
    """Extract potential entity names from free text using heuristics.

    This is deliberately lightweight — no NLP models, no spaCy.  It catches:
      - Proper nouns (capitalized word sequences)
      - Acronyms (2-6 uppercase letters)
      - CamelCase identifiers

    Args:
        text: Raw input text.

    Returns:
        Deduplicated list of extracted entity strings.
    """
    matches = _ENTITY_RE.findall(text)
    seen = set()  # type: set
    result = []  # type: List[str]
    for m in matches:
        m = m.strip()
        if m in _STOP_ENTITIES or len(m) < 2:
            continue
        key = m.lower()
        if key not in seen:
            seen.add(key)
            result.append(m)
    return result


# ---------------------------------------------------------------------------
# UUID generation
# ---------------------------------------------------------------------------

def new_id() -> str:
    """Generate a new UUID4 string for memory/edge IDs."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Database connection & schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
-- Memories table: stores content, embedding, and metadata
CREATE TABLE IF NOT EXISTS memories (
    id              TEXT PRIMARY KEY,
    content         TEXT    NOT NULL,
    embedding       BLOB,
    created_at      REAL    NOT NULL,
    last_accessed   REAL    NOT NULL,
    access_count    INTEGER NOT NULL DEFAULT 0,
    importance      REAL    NOT NULL DEFAULT 0.5,
    type            TEXT    NOT NULL DEFAULT 'episodic'
        CHECK (type IN ('episodic', 'semantic')),
    decayed         INTEGER NOT NULL DEFAULT 0
);

-- Graph edges: lightweight knowledge graph
CREATE TABLE IF NOT EXISTS edges (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target      TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relation    TEXT NOT NULL DEFAULT 'relates_to',
    weight      REAL NOT NULL DEFAULT 1.0,
    created_at  REAL NOT NULL
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_memories_type      ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);
CREATE INDEX IF NOT EXISTS idx_memories_decayed    ON memories(decayed);
CREATE INDEX IF NOT EXISTS idx_memories_last_accessed ON memories(last_accessed);
CREATE INDEX IF NOT EXISTS idx_edges_source        ON edges(source);
CREATE INDEX IF NOT EXISTS idx_edges_target        ON edges(target);
"""


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open (or create) the SQLite database and ensure the schema exists.

    Enables WAL mode for concurrent read/write safety and sets a 5-second
    busy timeout so parallel CLI calls don't immediately fail.

    Args:
        db_path: Path to the SQLite file.  Falls back to DEFAULT_DB_PATH.

    Returns:
        sqlite3.Connection with row_factory = sqlite3.Row.
    """
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    conn = sqlite3.connect(path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn
