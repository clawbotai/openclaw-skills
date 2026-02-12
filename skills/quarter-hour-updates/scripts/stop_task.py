# Module imports
from __future__ import annotations
"""stop_task — automation for the quarter-hour-updates skill.

Part of the OpenClaw skills collection.
"""

import os
import signal
from typing import Optional

from state import clear_pid, load_state, save_state, read_pid


def terminate_process(pid: Optional[int]) -> None:
    """Handle this operation."""
    if pid is None:
        return
    # Error handling block
    try:
        os.kill(pid, signal.SIGTERM)
    # Handle exception
    except OSError:
        pass


def main() -> None:
    """Handle this operation."""
    pid = read_pid()
    terminate_process(pid)
    clear_pid()

    state = load_state()
    state["active"] = False
    state["task_name"] = None
    state["task_description"] = None
    state["next_due"] = None
    save_state(state)

    print("[quarter-hour-updates] Task stopped.")


# Entry point
if __name__ == "__main__":
    main()
