"""CLI entry point for Project B.A.N."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer
import yaml
from rich.console import Console

from src.boundaries.b4_sanitizer import restore_all_disabled
from src.orchestrator import run_ban
from src.schemas import BanPayload
from src.ssh_manager import SSHManager

app = typer.Typer(
    name="ban",
    help="Project B.A.N. — Bare-metal Autonomous Node",
    no_args_is_help=True,
)
console = Console()


def _load_config(config_path: str) -> BanPayload:
    """Load and validate a YAML config file into a BanPayload."""
    path = Path(config_path).expanduser()
    if not path.is_file():
        console.print(f"[bold red]Error:[/] Config file not found: {path}")
        raise typer.Exit(code=1)

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        console.print("[bold red]Error:[/] Config file must be a YAML mapping")
        raise typer.Exit(code=1)

    try:
        return BanPayload(**raw)
    except Exception as exc:
        console.print(f"[bold red]Validation error:[/] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def strip(
    config: str = typer.Argument(..., help="Path to ban_payload.yaml config file"),
) -> None:
    """Run the full B.A.N. pipeline: profile → anchor → strip → launch."""
    payload = _load_config(config)
    run_ban(payload)


@app.command()
def validate(
    config: str = typer.Argument(..., help="Path to ban_payload.yaml config file"),
) -> None:
    """Validate a config file without executing anything."""
    payload = _load_config(config)
    console.print("[bold green]✓ Config is valid[/]\n")
    console.print(f"  [dim]Target:[/]     {payload.target_host}")
    console.print(f"  [dim]User:[/]       {payload.ssh_user}")
    console.print(f"  [dim]Binary:[/]     {payload.target_binary}")
    console.print(f"  [dim]Nice:[/]       {payload.nice_value}")
    console.print(f"  [dim]DMS timeout:[/] {payload.dead_mans_switch_timeout}s")
    console.print(f"  [dim]Allowlist:[/]  {len(payload.merged_allowlist)} daemons")
    for daemon in payload.merged_allowlist:
        console.print(f"    • {daemon}")
    console.print()


@app.command()
def restore(
    config: str = typer.Argument(..., help="Path to ban_payload.yaml config file"),
) -> None:
    """Restore all disabled daemons on the target (nuclear rollback).

    Use this if B.A.N. stripped a machine and you need to undo it.
    launchctl disable is PERSISTENT across reboots — this is the only
    way to undo it without manually re-enabling each daemon.
    """
    payload = _load_config(config)
    console.print("[bold yellow]Connecting to target for rollback…[/]")
    try:
        with SSHManager(
            host=payload.target_host,
            user=payload.ssh_user,
            key_path=payload.ssh_key_path,
            password=payload.ssh_password,
        ) as ssh:
            actions = restore_all_disabled(ssh)
            console.print(f"[bold green]✓ Re-enabled {len(actions)} daemon(s)[/]")
            console.print("[yellow]Reboot the target to fully restore all services.[/]")
    except Exception as exc:
        console.print(f"[bold red]Restore failed:[/] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def health(
    config: str = typer.Argument("ban_payload.yaml", help="Path to config file"),
) -> None:
    """Check operational readiness: dependencies and config validity."""
    console.print("[bold]Checking B.A.N. operational health...[/]\n")

    # 1. Local Dependencies
    ssh_path = shutil.which("ssh")
    if ssh_path:
        console.print(f"[green]✓[/] Found ssh binary: [dim]{ssh_path}[/]")
    else:
        console.print(
            "[yellow]![/] ssh binary not found in PATH (Paramiko usage unaffected, "
            "but recommended for debugging)[/]"
        )

    # 2. Config Validation
    path = Path(config).expanduser()
    if path.is_file():
        # _load_config raises Exit(1) on failure, which is what we want
        _load_config(str(path))
        console.print(f"[green]✓[/] Config file valid: [dim]{path}[/]")
    else:
        console.print(f"[red]✗[/] Config file missing: {path}")
        raise typer.Exit(code=1)

    console.print("\n[bold green]System Ready.[/]")


if __name__ == "__main__":
    app()
