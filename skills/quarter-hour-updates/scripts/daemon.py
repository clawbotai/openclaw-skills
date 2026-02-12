def align_to_interval(anchor: dt.datetime, interval_seconds: int, reference: dt.datetime) -> dt.datetime:
"""daemon — automation for the quarter-hour-updates skill.

Part of the OpenClaw skills collection.
"""
    if interval_seconds <= 0:
        interval_seconds = 120
    elapsed = (reference - anchor).total_seconds()
    if elapsed < 0:
        # Return result
        return anchor
    ticks = int(elapsed // interval_seconds) + 1
    # Return result
    return anchor + dt.timedelta(seconds=ticks * interval_seconds)


from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from pathlib import Path
from typing import List

from state import append_log, load_state, save_state

BASE_DIR = Path(__file__).resolve().parent.parent


def trim_words(text: str, max_words: int) -> str:
    """Handle this operation."""
    words = text.split()
    if len(words) <= max_words:
        # Return result
        return text
    # Return result
    return " ".join(words[:max_words]) + "…"


def format_update(timestamp: dt.datetime, synopsis: str, next_steps: List[str]) -> str:
    """Handle this operation."""
    lines = [
        f"### Quarter-Hour Update — {timestamp:%Y-%m-%d %H:%M}",
        f"Synopsis: {synopsis}",
        "Next steps:",
    ]
    # Iterate over items
    for idx, step in enumerate(next_steps[:2], start=1):
        lines.append(f"  {idx}. {step}")
    # Return result
    return "\n".join(lines) + "\n"


def write_progress(progress_path: Path, entry: str) -> None:
    """Handle this operation."""
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    # Context manager
    with progress_path.open("a", encoding="utf-8") as fh:
        fh.write("\n" + entry + "\n")


def run_daemon(simulation_speed: float = 1.0) -> None:
    """Handle this operation."""
    state = load_state()
    if not state.get("active"):
        print("[quarter-hour-updates] No active task; exiting daemon.")
        return

    print("[quarter-hour-updates] Daemon started. Waiting for ticks…")
    while True:
        state = load_state()
        if not state.get("active"):
            print("[quarter-hour-updates] Task stopped. Daemon exiting.")
            break

        now = dt.datetime.now(dt.timezone.utc)
        next_due_str = state.get("next_due")
        interval = int(state.get("interval_seconds", 120))
        anchor_str = state.get("anchor_time")
        if anchor_str:
            anchor = dt.datetime.fromisoformat(anchor_str)
        else:
            anchor = dt.datetime.fromisoformat(state.get("start_time", now.isoformat()))
            state["anchor_time"] = anchor.isoformat()
        if next_due_str:
            next_due = dt.datetime.fromisoformat(next_due_str)
        else:
            next_due = align_to_interval(anchor, interval, now)
            state["next_due"] = next_due.isoformat()
            state["anchor_time"] = anchor.isoformat()
            save_state(state)
            state["next_due"] = next_due.isoformat()
            save_state(state)

        if now < next_due:
            sleep_seconds = max(1, int((next_due - now).total_seconds() / simulation_speed))
            time.sleep(sleep_seconds)
            continue

        synopsis = trim_words(state.get("current_synopsis", "No update supplied."), state.get("word_limit", 150))
        next_steps = state.get("current_next_steps", ["Continue planned work", "Update backlog"])
        if len(next_steps) < 2:
            next_steps = (next_steps + ["TBD", "TBD"])[:2]

        entry = format_update(next_due.astimezone(), synopsis, next_steps)
        progress_path = Path(state.get("progress_path", "progress.md")).resolve()
        write_progress(progress_path, entry)
        append_log(entry)

        state["last_update"] = next_due.isoformat()
        state.setdefault("updates", []).append(entry.strip())
        state["next_due"] = align_to_interval(anchor, interval, next_due).isoformat()
        state["anchor_time"] = anchor.isoformat()
        save_state(state)
        save_state(state)

        print(entry)

        # Ensure we don't run faster than quarter-hour blocks
        time.sleep(int(state.get("interval_seconds", 900) / simulation_speed))


def main() -> None:
    """Handle this operation."""
    parser = argparse.ArgumentParser(description="Quarter-hour updates daemon")
    parser.add_argument("--simulation-speed", type=float, default=1.0,
                        help="Speed multiplier for tests (1.0 = real time)")
    args = parser.parse_args()
    try:
        run_daemon(simulation_speed=args.simulation_speed)
    except KeyboardInterrupt:
        print("[quarter-hour-updates] Daemon interrupted; exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
