"""Boundary 4 — Daemon strip-down (the actual stripping).

CRITICAL: launchctl disable system/ is PERSISTENT across reboots on modern macOS.
Rollback MUST explicitly call launchctl enable for each disabled daemon.

OPTIMIZATION: All bootout+disable commands are batched into a single SSH call
to avoid excessive round-trips (previously 2 calls × N daemons).
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.schemas import IMMUTABLE_CORE_DAEMONS
from src.ssh_manager import SSHManager


def _query_active_daemons(ssh: SSHManager) -> set[str]:
    """Return the set of currently active system daemon labels."""
    exit_code, stdout, stderr = ssh.execute_command(
        "launchctl list | awk 'NR>1 {print $3}'", sudo=True
    )
    if exit_code != 0:
        raise RuntimeError(f"Failed to list daemons (exit {exit_code}): {stderr.strip()}")

    daemons: set[str] = set()
    for line in stdout.strip().splitlines():
        label = line.strip()
        if label and label != "-":
            daemons.add(label)
    return daemons


def execute_strip_down(ssh: SSHManager, merged_allowlist: list[str]) -> list[dict[str, str]]:
    """Strip all daemons not in the merged allowlist.

    All bootout+disable commands are batched into a single SSH call
    for performance (avoids 2×N round-trips).
    """
    active = _query_active_daemons(ssh)
    allowset = set(merged_allowlist)
    bloatware = sorted(active - allowset)

    # SAFETY CHECK — immutable daemons must NEVER appear in the kill list
    immutable_set = set(IMMUTABLE_CORE_DAEMONS)
    endangered = set(bloatware) & immutable_set
    if endangered:
        raise RuntimeError(
            f"HARD ABORT: immutable core daemons targeted for removal: {sorted(endangered)}"
        )

    if not bloatware:
        return []

    # Build a single batched command for all daemons
    cmds: list[str] = []
    for daemon in bloatware:
        cmds.append(f"launchctl bootout system/{daemon} 2>/dev/null || true")
        cmds.append(f"launchctl disable system/{daemon} 2>/dev/null || true")

    batch = " && ".join(cmds)
    ssh.execute_command(batch, sudo=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    actions: list[dict[str, str]] = [
        {"daemon": d, "action": "bootout+disable", "timestamp": timestamp}
        for d in bloatware
    ]

    # Post-strip verification — some daemons respawn; warn but proceed
    remaining = _query_active_daemons(ssh)
    unexpected = remaining - allowset
    if unexpected:
        warn_ts = datetime.now(timezone.utc).isoformat()
        for d in sorted(unexpected):
            actions.append({
                "daemon": d,
                "action": "warning:still_active_after_strip",
                "timestamp": warn_ts,
            })

    return actions


def restore_daemons(ssh: SSHManager, disabled_daemons: list[str]) -> list[dict[str, str]]:
    """Re-enable previously disabled daemons (batched)."""
    if not disabled_daemons:
        return []

    batch = " && ".join(
        f"launchctl enable system/{d} 2>/dev/null || true"
        for d in sorted(disabled_daemons)
    )
    ssh.execute_command(batch, sudo=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    return [
        {"daemon": d, "action": "re-enabled", "timestamp": timestamp}
        for d in sorted(disabled_daemons)
    ]


def restore_all_disabled(ssh: SSHManager) -> list[dict[str, str]]:
    """Query all disabled daemons and re-enable them via a script on the target.

    Uses a remote script to avoid SSH command length/timeout issues
    with hundreds of daemons.
    """
    import base64

    exit_code, stdout, _ = ssh.execute_command(
        "launchctl print-disabled system", sudo=True
    )
    if exit_code != 0:
        return []

    daemons: list[str] = []
    for line in stdout.splitlines():
        if "disabled" in line and "=>" in line:
            parts = line.strip().strip('"').split('"')
            if parts:
                label = parts[0].strip().strip('"')
                if label:
                    daemons.append(label)

    if not daemons:
        return []

    # Build a restore script and run it on the target
    lines = ["#!/bin/bash"]
    for d in sorted(daemons):
        lines.append(f'launchctl enable system/{d} 2>/dev/null || true')
    lines.append("echo RESTORE_DONE")
    script = "\n".join(lines) + "\n"
    encoded = base64.b64encode(script.encode()).decode()

    # Write and execute
    ssh.execute_command(
        f"bash -c 'echo {encoded} | base64 -d > /tmp/ban_restore.sh && "
        f"chmod +x /tmp/ban_restore.sh'",
        sudo=True,
    )
    ssh.execute_command("/tmp/ban_restore.sh", sudo=True, timeout=120)
    ssh.execute_command("rm -f /tmp/ban_restore.sh", sudo=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    return [
        {"daemon": d, "action": "re-enabled", "timestamp": timestamp}
        for d in sorted(daemons)
    ]
