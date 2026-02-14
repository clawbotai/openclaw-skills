"""FSM orchestrator — drives the B.A.N. state machine from DRESSED to NIRVANA."""

from __future__ import annotations

import socket
import sys
import traceback
from enum import Enum

import paramiko
from rich.console import Console

from src.audit import AuditLog
from src.boundaries.b2_profiler import verify_target_anatomy
from src.boundaries.b3_anchor import arm_dead_mans_switch, create_snapshot, disarm_dead_mans_switch
from src.boundaries.b4_sanitizer import execute_strip_down
from src.boundaries.b5_qos import launch_bare_metal
from src.exceptions import BanError, DeterministicError, TransientError
from src.schemas import BanPayload
from src.ssh_manager import SSHManager


class BanState(str, Enum):
    DRESSED = "DRESSED"
    PEEPING = "PEEPING"
    PINNED = "PINNED"
    STRIPPING = "STRIPPING"
    BARE_METAL = "BARE_METAL"
    NIRVANA = "NIRVANA"
    ABORTED = "ABORTED"


console = Console()


def _transition(audit: AuditLog, current: BanState, target: BanState) -> BanState:
    """Log and execute a state transition."""
    audit.record_state_transition(current.value, target.value)
    console.print(f"  [bold cyan]▸[/] {current.value} → [bold green]{target.value}[/]")
    return target


def run_ban(config: BanPayload) -> None:
    """Execute the full B.A.N. finite state machine."""
    audit = AuditLog()
    state = BanState.DRESSED
    strip_only = config.target_binary is None

    console.print("\n[bold magenta]╔══════════════════════════════════════╗[/]")
    console.print("[bold magenta]║   Project B.A.N. — Engaging FSM     ║[/]")
    console.print("[bold magenta]╚══════════════════════════════════════╝[/]\n")

    if strip_only:
        console.print("[yellow]Mode: STRIP-ONLY (no workload binary specified)[/]\n")

    try:
        # ── STATE 0: DRESSED → PEEPING (connect + verify) ──
        console.print("[bold yellow]STATE 1:[/] Profiling target anatomy…")
        with SSHManager(
            host=config.target_host,
            user=config.ssh_user,
            key_path=config.ssh_key_path,
            password=config.ssh_password,
        ) as ssh:
            state = _transition(audit, state, BanState.PEEPING)

            # If verify_target_anatomy raises DeterministicError (e.g. anatomy mismatch),
            # it will be caught by the main BanError block.
            verify_target_anatomy(ssh, config)

            # ── STATE 1: PEEPING → PINNED (snapshot + DMS) ──
            console.print("[bold yellow]STATE 2:[/] Anchoring snapshot & arming DMS…")
            state = _transition(audit, state, BanState.PINNED)

            snapshot_id: str = "none"
            if config.skip_snapshot:
                console.print("  [yellow]Snapshot skipped (skip_snapshot=true)[/]")
            else:
                snapshot_id = create_snapshot(ssh)
                audit.record_snapshot(snapshot_id)
                console.print(f"  [dim]Snapshot:[/] {snapshot_id}")

            dms_pid = arm_dead_mans_switch(ssh, snapshot_id, config.dead_mans_switch_timeout)
            audit.record_dms_armed(dms_pid, config.dead_mans_switch_timeout)
            console.print(
                f"  [dim]DMS PID:[/] {dms_pid} "
                f"(timeout {config.dead_mans_switch_timeout}s)"
            )

            # ── States 2+ wrapped for SSH-loss recovery via DMS ──
            try:
                # ── STATE 2: PINNED → STRIPPING ──
                console.print("[bold yellow]STATE 3:[/] Stripping daemons…")
                state = _transition(audit, state, BanState.STRIPPING)

                actions = execute_strip_down(ssh, config.merged_allowlist)
                audit.record_disabled_daemons(actions)
                console.print(f"  [dim]Stripped {len(actions)} daemon(s)[/]")

                if strip_only:
                    # Skip workload launch — go straight to BARE_METAL → NIRVANA
                    console.print(
                        "[bold yellow]STATE 4:[/] Strip-only mode — "
                        "skipping workload launch…"
                    )
                    state = _transition(audit, state, BanState.BARE_METAL)
                else:
                    # ── STATE 3: STRIPPING → BARE_METAL ──
                    console.print(
                        "[bold yellow]STATE 4:[/] Launching bare-metal workload…"
                    )
                    state = _transition(audit, state, BanState.BARE_METAL)

                    workload_pid = launch_bare_metal(ssh, config)
                    audit.record_payload_launch(
                        workload_pid, config.target_binary or ""
                    )
                    console.print(f"  [dim]Workload PID:[/] {workload_pid}")

            except (paramiko.SSHException, socket.timeout, OSError) as exc:
                # Fallback legacy catch for raw socket errors not wrapped by SSHManager
                # or if SSHManager raises TransientError which we handle below, but here
                # we specifically want to message the DMS recovery.
                console.print(f"\n[bold red]SSH LOST:[/] {exc}")
                console.print(
                    "[yellow]Dead Man's Switch will handle recovery.[/]"
                )
                # Re-raise to be caught by main BanError/Exception blocks for auditing
                raise TransientError(f"SSH connection lost: {exc}") from exc

            # ── BARE_METAL → NIRVANA ──
            console.print("[bold yellow]STATE 5:[/] Disarming DMS — entering NIRVANA…")
            disarmed = disarm_dead_mans_switch(ssh, dms_pid)
            if disarmed:
                console.print("  [dim]DMS disarmed successfully[/]")
            else:
                console.print(
                    "  [yellow]DMS disarm returned non-zero "
                    "(may already be dead)[/]"
                )

            state = _transition(audit, state, BanState.NIRVANA)

        path = audit.finalize(state.value)
        console.print("\n[bold green]✓ B.A.N. complete — NIRVANA achieved[/]")
        console.print(f"[dim]Audit log:[/] {path}\n")

    except BanError as exc:
        # Structured error handling for known failure modes
        error_type = "deterministic" if isinstance(exc, DeterministicError) else "transient"
        color = "red" if isinstance(exc, DeterministicError) else "yellow"
        
        console.print(f"\n[bold {color}]{error_type.upper()} ERROR:[/] {exc}")
        
        # If it's a TransientError at this level, we abort the run but log it as transient
        # allowing upstream automations to decide on retry.
        
        audit.record_failure(
            error_type=error_type,
            message=str(exc),
            context=getattr(exc, "context", None),
            traceback=traceback.format_exc()
        )
        
        state = _transition(audit, state, BanState.ABORTED)
        path = audit.finalize(state.value)
        console.print(f"[dim]Audit log:[/] {path}")
        sys.exit(1)

    except Exception as exc:
        # Catch-all for unhandled/unknown errors (treated as Deterministic/Fatal)
        console.print(f"\n[bold red]UNHANDLED FATAL ERROR:[/] {exc}")
        console.print(traceback.format_exc())
        
        audit.record_failure(
            error_type="deterministic",
            message=f"Unhandled exception: {exc}",
            traceback=traceback.format_exc()
        )
        
        state = _transition(audit, state, BanState.ABORTED)
        path = audit.finalize(state.value)
        console.print(f"[dim]Audit log:[/] {path}")
        sys.exit(1)
