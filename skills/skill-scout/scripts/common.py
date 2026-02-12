"""Shared infrastructure for skill-scout: database access, shell execution, and logging.

Provides thread-safe SQLite access in WAL mode, a subprocess wrapper that
separates stdout (data) from stderr (diagnostics), and a pre-configured
logger that writes exclusively to stderr so stdout remains reserved for
JSON output.
"""

import json
import logging
import os
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Logging — all diagnostic output goes to stderr; stdout is for JSON only
# ---------------------------------------------------------------------------

_log_handler = logging.StreamHandler(sys.stderr)
_log_handler.setFormatter(logging.Formatter(
    "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
))

logger = logging.getLogger("skill-scout")
logger.addHandler(_log_handler)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolve workspace root relative to this file:
#   scripts/common.py -> skills/skill-scout/scripts/ -> workspace is 3 up
_SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = _SCRIPT_DIR.parent.parent.parent  # /Users/clawai/openclaw/workspace
SKILLS_DIR = WORKSPACE_ROOT / "skills"
SCOUT_DATA_DIR = WORKSPACE_ROOT / "memory" / "skill-scout"
DB_PATH = SCOUT_DATA_DIR / "scout.db"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

_DB_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS skills (
    slug TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_url TEXT,
    author TEXT,
    version TEXT,
    description TEXT,
    category TEXT,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    last_updated TEXT,
    content_hash TEXT,
    first_seen TEXT NOT NULL,
    last_evaluated TEXT,
    quality_score REAL,
    quality_tier TEXT,
    installed INTEGER DEFAULT 0,
    flagged INTEGER DEFAULT 0,
    raw_data TEXT
);

CREATE TABLE IF NOT EXISTS developers (
    username TEXT PRIMARY KEY,
    tier TEXT,
    score REAL,
    skill_count INTEGER DEFAULT 0,
    avg_skill_quality REAL,
    last_activity TEXT,
    watched INTEGER DEFAULT 0,
    raw_data TEXT
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    overall_score REAL NOT NULL,
    tier TEXT NOT NULL,
    dimension_scores TEXT NOT NULL,
    security_flags TEXT,
    notes TEXT,
    FOREIGN KEY (slug) REFERENCES skills(slug)
);

CREATE INDEX IF NOT EXISTS idx_skills_quality ON skills(quality_score);
CREATE INDEX IF NOT EXISTS idx_skills_source ON skills(source);
CREATE INDEX IF NOT EXISTS idx_skills_author ON skills(author);
CREATE INDEX IF NOT EXISTS idx_evaluations_slug ON evaluations(slug);
"""

# Global write lock: SQLite WAL allows concurrent reads but serializes writes.
# We use a Python-level lock rather than relying solely on SQLite's busy_timeout
# because the Python sqlite3 module's internal locking is per-connection, and
# our thread-local pattern means each thread has its own connection.
_write_lock = threading.Lock()

# Thread-local storage for database connections.  Each thread gets its own
# sqlite3 connection to avoid the "ProgrammingError: SQLite objects created
# in a thread can only be used in that same thread" restriction.
_local = threading.local()


def _ensure_dir() -> None:
    """Create the scout data directory if it does not exist."""
    SCOUT_DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    """Return a thread-local SQLite connection in WAL mode.

    Creates the database and schema on first access.  Each thread gets its
    own connection (required by sqlite3's thread-safety model) but all share
    the same WAL-mode database, allowing concurrent reads during writes.

    Returns:
        A ``sqlite3.Connection`` with ``row_factory`` set to
        ``sqlite3.Row`` for dict-like access.
    """
    conn = getattr(_local, "conn", None)
    if conn is not None:
        return conn

    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")

    # Run schema idempotently
    for stmt in _DB_SCHEMA.split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()

    _local.conn = conn
    return conn


def db_write(sql: str, params: tuple = ()) -> None:
    """Execute a write statement under the global write lock.

    Args:
        sql: SQL statement to execute.
        params: Bind parameters for the statement.
    """
    with _write_lock:
        conn = get_db()
        conn.execute(sql, params)
        conn.commit()


def db_write_many(sql: str, param_list: List[tuple]) -> None:
    """Execute a write statement for many rows under the global write lock.

    Args:
        sql: SQL statement to execute.
        param_list: List of bind-parameter tuples.
    """
    with _write_lock:
        conn = get_db()
        conn.executemany(sql, param_list)
        conn.commit()


def db_read(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a read query and return results as a list of dicts.

    Args:
        sql: SQL query to execute.
        params: Bind parameters.

    Returns:
        A list of dictionaries, one per row.
    """
    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Shell wrapper
# ---------------------------------------------------------------------------

class ShellError(Exception):
    """Raised when a subprocess exits with a non-zero return code."""

    def __init__(self, cmd: List[str], returncode: int, stderr: str):
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Command {cmd[0]} exited {returncode}: {stderr[:200]}")


def run_shell(cmd: List[str], timeout: int = 60) -> Dict[str, Any]:
    """Execute a shell command and return parsed output.

    Stdout is captured and returned as ``stdout`` (raw string) and, if
    parseable, as ``json`` (parsed object).  Stderr goes to ``stderr``.

    Args:
        cmd: Command and arguments as a list of strings.
        timeout: Maximum seconds to wait (default 60).

    Returns:
        Dict with keys ``stdout``, ``stderr``, ``returncode``, and
        optionally ``json`` if stdout is valid JSON.

    Raises:
        ShellError: If the process exits with a non-zero return code.
    """
    logger.debug("shell: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise ShellError(cmd, -1, f"Command not found: {cmd[0]}")
    except subprocess.TimeoutExpired:
        raise ShellError(cmd, -2, f"Timed out after {timeout}s")

    out: Dict[str, Any] = {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }

    if result.returncode != 0:
        raise ShellError(cmd, result.returncode, result.stderr)

    # Attempt JSON parse of stdout
    try:
        out["json"] = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        pass

    return out


def check_tool(name: str) -> bool:
    """Check whether an external CLI tool is available on PATH.

    Args:
        name: The command name to check (e.g. ``gh``, ``clawhub``).

    Returns:
        True if the tool exists, False otherwise.
    """
    try:
        result = subprocess.run(
            ["which", name],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def utcnow() -> str:
    """Return the current UTC time as an ISO 8601 string.

    Returns:
        ISO-formatted datetime string.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def json_out(data: Any) -> None:
    """Print a JSON object to stdout for agent consumption.

    This is the ONLY sanctioned way to write to stdout.  All other
    diagnostic or progress output must go through ``logger`` (stderr).

    Args:
        data: Any JSON-serializable Python object.
    """
    print(json.dumps(data, indent=2, default=str))


def content_hash(text: str) -> str:
    """Compute a SHA-256 hex digest of a text string.

    Args:
        text: The text to hash.

    Returns:
        64-character lowercase hex digest.
    """
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
