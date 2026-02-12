#!/usr/bin/env python3
"""
memory_client.py — Thin subprocess wrapper for agent-memory.

Provides a simple Python API for any skill to read/write the shared
vector memory store without importing agent-memory internals.

Usage:
    from lib.memory_client import remember, recall

    remember("Rebuilt email-manager with UID mode", importance=0.8)
    results = recall("email client changes", limit=3)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Resolve paths relative to workspace root (lib/ is one level down)
_WORKSPACE = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
_MEMORY_SCRIPT = os.path.join(
    _WORKSPACE, "skills", "agent-memory", "scripts", "memory.py"
)


def _run_memory_cmd(args: List[str], timeout: int = 60) -> Dict[str, Any]:
    """Execute a memory.py subcommand and return parsed JSON output.

    Args:
        args: Arguments to pass to memory.py (e.g. ["remember", "text"]).
        timeout: Max seconds to wait (embedding can be slow on first load).

    Returns:
        Parsed JSON dict from stdout.

    Raises:
        RuntimeError: If the command fails or returns invalid JSON.
    """
    cmd = [sys.executable, _MEMORY_SCRIPT] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_WORKSPACE,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"memory.py timed out after {timeout}s: {' '.join(args)}")
    except FileNotFoundError:
        raise RuntimeError(f"memory.py not found at {_MEMORY_SCRIPT}")

    # memory.py writes errors to stderr as JSON, success to stdout
    output = result.stdout.strip()
    if not output:
        output = result.stderr.strip()

    if not output:
        raise RuntimeError(
            f"memory.py returned no output (exit {result.returncode}): {' '.join(args)}"
        )

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError(f"memory.py returned invalid JSON: {output[:200]}")


def remember(
    text: str,
    importance: Optional[float] = None,
    memory_type: str = "episodic",
) -> Dict[str, Any]:
    """Store a memory with auto-embedding and entity extraction.

    Args:
        text: The text to remember.
        importance: Override importance (0.0-1.0). None = auto-calculated.
        memory_type: "episodic" (events) or "semantic" (facts).

    Returns:
        Dict with status, id, type, importance, entities, edges_created.
    """
    args = ["remember", text, "--type", memory_type]
    if importance is not None:
        args.extend(["--importance", str(importance)])
    return _run_memory_cmd(args)


def recall(query: str, limit: int = 7) -> List[Dict[str, Any]]:
    """Search memories using hybrid vector + graph scoring.

    Args:
        query: Natural-language search query.
        limit: Max results to return.

    Returns:
        List of scored memory dicts (content, score, type, etc.).
    """
    result = _run_memory_cmd(["recall", query, "--limit", str(limit)])
    return result.get("results", [])


def forget(memory_id: str) -> Dict[str, Any]:
    """Soft-delete a memory by ID.

    Args:
        memory_id: The UUID of the memory to decay.

    Returns:
        Dict with status and id.
    """
    return _run_memory_cmd(["forget", memory_id])


def relate(
    source_id: str,
    target_id: str,
    relation: str = "relates_to",
    weight: float = 1.0,
) -> Dict[str, Any]:
    """Create an explicit edge between two memories.

    Args:
        source_id: Source memory UUID.
        target_id: Target memory UUID.
        relation: Edge label (relates_to, contradicts, supersedes, etc.).
        weight: Edge weight (0.0-1.0).

    Returns:
        Dict with status, edge_id, source, target, relation, weight.
    """
    return _run_memory_cmd([
        "relate", source_id, target_id,
        "--relation", relation,
        "--weight", str(weight),
    ])


def stats() -> Dict[str, Any]:
    """Get memory system health report (instant, no model loading).

    Returns:
        Dict with total_memories, active, decayed, episodic, semantic, etc.
    """
    return _run_memory_cmd(["stats"], timeout=10)


def timeline(
    entity: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Retrieve memories in chronological order.

    Args:
        entity: Filter by entity/keyword.
        since: ISO 8601 date cutoff.
        limit: Max results.

    Returns:
        List of memory dicts in reverse chronological order.
    """
    args = ["timeline", "--limit", str(limit)]
    if entity:
        args.extend(["--entity", entity])
    if since:
        args.extend(["--since", since])
    result = _run_memory_cmd(args)
    return result.get("timeline", [])
