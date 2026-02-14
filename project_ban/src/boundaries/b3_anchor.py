"""Boundary 3 — Snapshot anchoring and Dead Man's Switch.

CRITICAL DESIGN NOTE: The DMS must re-enable all disabled daemons before rebooting,
because launchctl disable is PERSISTENT across reboots on modern macOS.

IMPLEMENTATION NOTE: To launch a persistent background process via sudo over SSH
(Paramiko), we must:
1. Write the script to disk via base64 (avoids heredoc/stdin conflicts with sudo -S)
2. Launch via: sudo bash -c 'nohup /script </dev/null >log 2>&1 & echo $!'
   The </dev/null fully detaches stdin so the process survives channel close.
"""

from __future__ import annotations

import base64
import re
import time

from src.ssh_manager import SSHManager

DMS_SCRIPT_PATH = "/tmp/ban_dms.sh"
DMS_PID_PATH = "/tmp/ban_dms.pid"
DMS_LOG_PATH = "/var/log/ban_dms.log"


def create_snapshot(ssh: SSHManager) -> str:
    """Create a local Time Machine snapshot and return the snapshot ID string."""
    exit_code, stdout, stderr = ssh.execute_command("tmutil localsnapshot", sudo=True)
    if exit_code != 0:
        raise RuntimeError(f"Failed to create TM snapshot (exit {exit_code}): {stderr.strip()}")

    match = re.search(r"(\d{4}-\d{2}-\d{2}-\d{6})", stdout)
    if not match:
        raise RuntimeError(f"Could not parse snapshot ID from tmutil output: {stdout.strip()}")

    return match.group(1)


def arm_dead_mans_switch(ssh: SSHManager, snapshot_id: str, timeout: int) -> int:
    """Deploy a detached Dead Man's Switch process.

    If not disarmed within `timeout` seconds, the DMS will:
    1. Re-enable ALL disabled system daemons (launchctl enable)
    2. Reboot the machine
    """
    # Build the DMS script — writes its own PID for reliable disarming
    dms_script = f"""#!/bin/bash
echo $$ > {DMS_PID_PATH}
sleep {timeout}
# Re-enable all disabled system daemons
launchctl print-disabled system 2>/dev/null | grep disabled | sed 's/.*"\\(.*\\)".*/\\1/' | while read svc; do
    launchctl enable system/"$svc" 2>/dev/null
done
# Reboot to restore all services
reboot
"""
    # Base64 encode to avoid quoting issues with sudo stdin
    encoded = base64.b64encode(dms_script.encode()).decode()

    # Write script to target via base64 decode
    write_cmd = (
        f"bash -c 'echo {encoded} | base64 -d > {DMS_SCRIPT_PATH} "
        f"&& chmod +x {DMS_SCRIPT_PATH}'"
    )
    exit_code, _, stderr = ssh.execute_command(write_cmd, sudo=True)
    if exit_code != 0:
        raise RuntimeError(f"Failed to write DMS script: {stderr.strip()}")

    # Launch detached — </dev/null ensures process survives SSH channel close
    launch_cmd = (
        f"bash -c 'nohup {DMS_SCRIPT_PATH} </dev/null "
        f">{DMS_LOG_PATH} 2>&1 & echo $!'"
    )
    exit_code, stdout, stderr = ssh.execute_command(launch_cmd, sudo=True)
    if exit_code != 0:
        raise RuntimeError(f"Failed to arm DMS (exit {exit_code}): {stderr.strip()}")

    # Give the script a moment to start and write its PID
    time.sleep(1)

    # Read the PID from the file the script wrote
    exit_code, pid_out, _ = ssh.execute_command(f"cat {DMS_PID_PATH}", sudo=True)
    if exit_code != 0:
        raise RuntimeError("DMS failed to write PID file — script may not have started")

    pid_str = pid_out.strip()
    try:
        pid = int(pid_str)
    except ValueError:
        raise RuntimeError(f"Could not parse DMS PID from {DMS_PID_PATH}: {pid_str}")

    # Verify the process is alive
    verify_code, _, _ = ssh.execute_command(f"kill -0 {pid}", sudo=True)
    if verify_code != 0:
        raise RuntimeError(f"DMS process {pid} is not alive after arming")

    return pid


def disarm_dead_mans_switch(ssh: SSHManager, dms_pid: int) -> bool:
    """Kill the Dead Man's Switch process. Returns True if successfully killed."""
    exit_code, _, _ = ssh.execute_command(f"kill -9 {dms_pid}", sudo=True)
    # Clean up
    ssh.execute_command(
        f"rm -f {DMS_SCRIPT_PATH} {DMS_PID_PATH}", sudo=True
    )
    return exit_code == 0
