"""Boundary 5 — Bare-metal workload launch with QoS priority."""

from __future__ import annotations

import time

from src.schemas import BanPayload
from src.ssh_manager import SSHManager


def launch_bare_metal(ssh: SSHManager, config: BanPayload) -> int:
    """Launch the target binary at bare-metal priority. Returns the workload PID."""
    cmd = (
        f"nohup nice -n {config.nice_value} caffeinate -s {config.target_binary} "
        f"> /var/log/ban_execution.log 2>&1 & echo $!"
    )
    exit_code, stdout, stderr = ssh.execute_command(cmd, sudo=True)
    if exit_code != 0:
        raise RuntimeError(f"Failed to launch workload (exit {exit_code}): {stderr.strip()}")

    pid_str = stdout.strip().splitlines()[-1]
    try:
        pid = int(pid_str)
    except ValueError:
        raise RuntimeError(f"Could not parse workload PID from output: {stdout.strip()}")

    # Wait for process to settle
    time.sleep(2)

    # Verify PID is alive
    verify_code, _, _ = ssh.execute_command(f"kill -0 {pid}", sudo=True)
    if verify_code != 0:
        # Grab last 20 lines of log for diagnostics
        _, log_tail, _ = ssh.execute_command("tail -20 /var/log/ban_execution.log", sudo=True)
        raise RuntimeError(
            f"Workload PID {pid} died after launch. Last 20 log lines:\n{log_tail.strip()}"
        )

    return pid
