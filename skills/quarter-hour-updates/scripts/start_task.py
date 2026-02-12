from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from state import load_state, save_state, store_pid

BASE_DIR = Path(__file__).resolve().parent


def align_to_interval(anchor: datetime, interval_seconds: int, reference: datetime) -> datetime:
    if interval_seconds <= 0:
        interval_seconds = 120
    elapsed = (reference - anchor).total_seconds()
    if elapsed < 0:
        elapsed = 0
    ticks = int(elapsed // interval_seconds) + 1
    return anchor + timedelta(seconds=ticks * interval_seconds)


def launch_daemon(simulation_speed: float = 1.0) -> int:
    daemon_path = BASE_DIR / "daemon.py"
    cmd = [sys.executable, str(daemon_path), "--simulation-speed", str(simulation_speed)]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    store_pid(process.pid)
    return process.pid


def main() -> None:
    parser = argparse.ArgumentParser(description="Start quarter-hour updates task")
    parser.add_argument("task_name", help="Display name of the active task")
    parser.add_argument("task_description", help="Short description of the task")
    parser.add_argument("--plan", default="task_plan.md")
    parser.add_argument("--progress", default="progress.md")
    parser.add_argument("--findings", default="findings.md")
    parser.add_argument("--simulation-speed", type=float, default=1.0,
                        help="Speed multiplier (use >1 for accelerated tests)")
    parser.add_argument("--interval-seconds", type=int, default=120,
                        help="Update frequency in seconds (default 120 for verification)")
    args = parser.parse_args()

    state = load_state()
    now = datetime.now(timezone.utc)
    interval = args.interval_seconds
    anchor = now.replace(second=0, microsecond=0)
    state.update({
        "active": True,
        "task_name": args.task_name,
        "task_description": args.task_description,
        "start_time": now.isoformat(),
        "anchor_time": anchor.isoformat(),
        "last_update": None,
        "next_due": None,
        "plan_path": str(Path(args.plan).resolve()),
        "progress_path": str(Path(args.progress).resolve()),
        "findings_path": str(Path(args.findings).resolve()),
        "current_synopsis": f"Task '{args.task_name}' kicked off.",
        "current_next_steps": ["Begin work", "Prepare first update"],
        "interval_seconds": args.interval_seconds,
    })
    state["next_due"] = align_to_interval(anchor, interval, now).isoformat()
    save_state(state)

    pid = launch_daemon(simulation_speed=args.simulation_speed)
    print(f"[quarter-hour-updates] Started daemon (pid={pid}).")


if __name__ == "__main__":
    main()
