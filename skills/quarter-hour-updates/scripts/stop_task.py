from __future__ import annotations

import os
import signal
from typing import Optional

from state import clear_pid, load_state, save_state, read_pid


def terminate_process(pid: Optional[int]) -> None:
    if pid is None:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass


def main() -> None:
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


if __name__ == "__main__":
    main()
