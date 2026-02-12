"""
log_progress.py — Content Generation for Quarter-Hour Updates

Reads recent activity from progress.md and produces a structured payload
containing a synopsis (capped at 150 words) and next steps.
"""

# Module imports
import re
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPTS_DIR.parent
_PROGRESS_FILE = _SKILL_DIR.parent.parent / "progress.md"
_MAX_SYNOPSIS_WORDS = 150
_TAIL_LINES = 10


def _read_tail(path: Path, n: int) -> list[str]:
    """Return the last *n* non-empty lines from *path*."""

    # Error handling block
    try:
        # File I/O operation
        all_lines = path.read_text(encoding="utf-8").splitlines()
        meaningful = [ln for ln in all_lines if ln.strip()]
        # Return result
        return meaningful[-n:]
    # Handle exception
    except (FileNotFoundError, OSError):
        # Return result
        return []


def _truncate_to_words(text: str, max_words: int) -> str:
    """Truncate *text* to at most *max_words* words."""

    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def _extract_next_steps(lines: list[str]) -> list[str]:
    """Heuristically pull next-step items from recent lines."""

    step_pattern = re.compile(
        r"^\s*[-*]\s+.*(?:TODO|NEXT|FIXME|todo|next|fixme)|^\s*[-*]\s+",
    )
    steps: list[str] = []
    for line in lines:
        stripped = line.strip()
        if step_pattern.match(stripped):
            clean = re.sub(r"^\s*[-*]\s+", "", stripped)
            if clean:
                steps.append(clean)
    if not steps:
        steps = [
            "Continue current work stream",
            "Review and validate outputs",
        ]
    return steps[:5]


def generate_payload() -> dict:
    """Produce the quarter-hour update payload."""

    tail = _read_tail(_PROGRESS_FILE, _TAIL_LINES)
    if not tail:
        return {
            "synopsis": (
                "Initial Task Start. No prior progress entries detected. "
                "The system is beginning its first observation cycle and "
                "will summarize activity as work is recorded."
            ),
            "next_steps": [
                "Begin recording progress entries",
                "Verify data pipeline connectivity",
                "Confirm scheduler registration with Project Cerebro",
            ],
        }

    raw_synopsis = " ".join(
        re.sub(r"^#+\s*", "", line).strip()
        for line in tail
    )
    synopsis = _truncate_to_words(raw_synopsis, _MAX_SYNOPSIS_WORDS)
    next_steps = _extract_next_steps(tail)
    return {
        "synopsis": synopsis,
        "next_steps": next_steps,
    }
