#!/usr/bin/env python3
"""
agent-guardrails / snapshot.py
===============================
File rollback system for the guardrails safety layer.

Before the agent modifies a file (T2+ actions), a snapshot is saved.
If something goes wrong, the snapshot can be restored.

Snapshots are stored in .guardrails/snapshots/ with metadata in a
JSON sidecar file.  Auto-prunes after 7 days (configurable).

Commands:
    save <filepath>          Save a snapshot before modification
    restore <snapshot_id>    Restore a file from snapshot
    list                     List available snapshots
    prune [--days N]         Delete snapshots older than N days
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SKILL_DIR = Path(__file__).resolve().parent.parent  # .../skills/agent-guardrails
_WORKSPACE = _SKILL_DIR.parent.parent  # .../skills/../ = workspace root
_SNAPSHOT_DIR = _WORKSPACE / ".guardrails" / "snapshots"
_META_FILE = _WORKSPACE / ".guardrails" / "snapshots.json"

# Max file size for snapshots (100MB default)
_MAX_SIZE_BYTES = 100 * 1024 * 1024


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _json_out(data: Any) -> None:
    """Print structured JSON to stdout."""
    print(json.dumps(data, indent=2, default=str))


def _error_out(message: str, code: str = "ERROR") -> None:
    """Print a JSON error to stderr and exit 1."""
    print(json.dumps({"status": "error", "code": code, "message": message}),
          file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Metadata management
# ---------------------------------------------------------------------------

def _load_meta() -> Dict[str, Any]:
    """Load the snapshots metadata file.

    Returns:
        Dict with "snapshots" key containing a list of snapshot records.
    """
    if _META_FILE.exists():
        try:
            with open(_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"snapshots": []}


def _save_meta(meta: Dict[str, Any]) -> None:
    """Write the snapshots metadata file."""
    os.makedirs(_META_FILE.parent, exist_ok=True)
    with open(_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)


def _generate_snapshot_id(filepath: str) -> str:
    """Generate a short unique ID based on filepath + timestamp.

    Format: first 8 chars of SHA256(filepath:timestamp).
    """
    raw = f"{filepath}:{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# SAVE — snapshot a file before modification
# ---------------------------------------------------------------------------

def cmd_save(args: argparse.Namespace) -> None:
    """Save a snapshot of a file before the agent modifies it.

    Checks:
      - File exists
      - File size < 100MB (prevents disk fill from snapshotting large binaries)
      - Creates a copy in .guardrails/snapshots/

    Args:
        args: Parsed CLI args with .filepath (str).
    """
    filepath = args.filepath
    real_path = os.path.realpath(os.path.expanduser(filepath))

    if not os.path.exists(real_path):
        _error_out(f"File not found: {filepath}", "FILE_NOT_FOUND")

    if not os.path.isfile(real_path):
        _error_out(f"Not a regular file: {filepath}", "NOT_FILE")

    file_size = os.path.getsize(real_path)
    if file_size > _MAX_SIZE_BYTES:
        _json_out({
            "status": "skipped",
            "reason": f"File too large ({file_size / 1024 / 1024:.1f}MB > 100MB limit)",
            "filepath": filepath,
        })
        return

    # Create snapshot
    snapshot_id = _generate_snapshot_id(real_path)
    os.makedirs(_SNAPSHOT_DIR, exist_ok=True)

    # Preserve extension for readability
    _, ext = os.path.splitext(filepath)
    snapshot_filename = f"{snapshot_id}{ext}"
    snapshot_path = _SNAPSHOT_DIR / snapshot_filename

    shutil.copy2(real_path, snapshot_path)

    # Record metadata
    meta = _load_meta()
    record = {
        "id": snapshot_id,
        "original_path": real_path,
        "snapshot_file": str(snapshot_path),
        "timestamp": time.time(),
        "file_size": file_size,
    }
    meta["snapshots"].append(record)
    _save_meta(meta)

    _json_out({
        "status": "saved",
        "id": snapshot_id,
        "original_path": real_path,
        "snapshot_path": str(snapshot_path),
        "file_size": file_size,
    })


# ---------------------------------------------------------------------------
# RESTORE — recover a file from snapshot
# ---------------------------------------------------------------------------

def cmd_restore(args: argparse.Namespace) -> None:
    """Restore a file from a saved snapshot.

    Copies the snapshot back to the original path, creating parent
    directories if needed.

    Args:
        args: Parsed CLI args with .snapshot_id (str).
    """
    meta = _load_meta()
    target_id = args.snapshot_id

    record = None
    for snap in meta["snapshots"]:
        if snap["id"] == target_id:
            record = snap
            break

    if not record:
        _error_out(f"Snapshot not found: {target_id}", "NOT_FOUND")

    snapshot_path = record["snapshot_file"]
    if not os.path.exists(snapshot_path):
        _error_out(
            f"Snapshot file missing on disk: {snapshot_path}",
            "FILE_MISSING",
        )

    original_path = record["original_path"]
    os.makedirs(os.path.dirname(original_path), exist_ok=True)
    shutil.copy2(snapshot_path, original_path)

    _json_out({
        "status": "restored",
        "id": target_id,
        "restored_to": original_path,
        "from_snapshot": snapshot_path,
    })


# ---------------------------------------------------------------------------
# LIST — show available snapshots
# ---------------------------------------------------------------------------

def cmd_list(args: argparse.Namespace) -> None:
    """List all available snapshots with metadata."""
    meta = _load_meta()
    snapshots = meta.get("snapshots", [])

    # Verify each snapshot still exists on disk
    for snap in snapshots:
        snap["exists_on_disk"] = os.path.exists(snap.get("snapshot_file", ""))
        snap["age_hours"] = round((time.time() - snap.get("timestamp", 0)) / 3600, 1)

    limit = getattr(args, "limit", 20) or 20
    snapshots = sorted(snapshots, key=lambda s: s.get("timestamp", 0), reverse=True)

    _json_out({
        "status": "ok",
        "count": len(snapshots),
        "snapshots": snapshots[:limit],
    })


# ---------------------------------------------------------------------------
# PRUNE — delete old snapshots
# ---------------------------------------------------------------------------

def cmd_prune(args: argparse.Namespace) -> None:
    """Delete snapshots older than N days.

    Args:
        args: Parsed CLI args with .days (int, default 7).
    """
    days = getattr(args, "days", 7) or 7
    cutoff = time.time() - (days * 86400)

    meta = _load_meta()
    keep = []  # type: List[Dict]
    pruned = 0

    for snap in meta.get("snapshots", []):
        if snap.get("timestamp", 0) < cutoff:
            # Delete the snapshot file
            snapshot_path = snap.get("snapshot_file", "")
            if os.path.exists(snapshot_path):
                try:
                    os.remove(snapshot_path)
                except OSError:
                    pass
            pruned += 1
        else:
            keep.append(snap)

    meta["snapshots"] = keep
    _save_meta(meta)

    # Calculate total disk usage of remaining snapshots
    total_size = sum(
        os.path.getsize(s["snapshot_file"])
        for s in keep
        if os.path.exists(s.get("snapshot_file", ""))
    )

    _json_out({
        "status": "pruned",
        "removed": pruned,
        "remaining": len(keep),
        "days_threshold": days,
        "disk_usage_bytes": total_size,
    })


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI for snapshot commands."""
    parser = argparse.ArgumentParser(
        prog="snapshot.py",
        description="File rollback system for agent-guardrails.",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    # save
    p_save = subs.add_parser("save", help="Snapshot a file before modification")
    p_save.add_argument("filepath", help="File to snapshot")

    # restore
    p_restore = subs.add_parser("restore", help="Restore a file from snapshot")
    p_restore.add_argument("snapshot_id", help="Snapshot ID to restore")

    # list
    p_list = subs.add_parser("list", help="List available snapshots")
    p_list.add_argument("--limit", type=int, default=20)

    # prune
    p_prune = subs.add_parser("prune", help="Delete old snapshots")
    p_prune.add_argument("--days", type=int, default=7,
                         help="Delete snapshots older than N days (default: 7)")

    return parser


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_DISPATCH = {
    "save": cmd_save,
    "restore": cmd_restore,
    "list": cmd_list,
    "prune": cmd_prune,
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
