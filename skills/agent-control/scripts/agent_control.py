#!/usr/bin/env python3
"""
Utility helpers for managing OpenClaw agent sessions and model defaults directly from skill workflows.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Path to the main OpenClaw configuration file
CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
# Root directory containing per-agent session and config data
AGENTS_ROOT = Path.home() / ".openclaw" / "agents"


def load_config() -> dict[str, Any]:
    """Load and parse the OpenClaw JSON config file.

    Returns:
        dict: The parsed configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found at {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())


def write_config(data: dict[str, Any]) -> None:
    """Serialize and persist the config back to disk."""
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n")


def cmd_status(_: argparse.Namespace) -> None:
    """Print a JSON summary of default and per-agent model assignments to stdout."""
    data = load_config()
    defaults = data.get("agents", {}).get("defaults", {})
    primary = defaults.get("model", {}).get("primary")
    fallbacks = defaults.get("model", {}).get("fallbacks", [])
    agents = {entry.get("id"): entry.get("model") for entry in data.get("agents", {}).get("list", [])}
    payload = {
        "default_primary": primary,
        "default_fallbacks": fallbacks,
        "agent_models": agents,
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_set_model(args: argparse.Namespace) -> None:
    """Update the primary model (and optional fallbacks) for an agent in the config file."""
    data = load_config()
    agents_blob = data.setdefault("agents", {})
    defaults = agents_blob.setdefault("defaults", {})
    defaults_model = defaults.setdefault("model", {})
    defaults_model["primary"] = args.model
    if args.fallbacks is not None:
        defaults_model["fallbacks"] = [fallback.strip() for fallback in args.fallbacks.split(",") if fallback.strip()]
    models_map = defaults.setdefault("models", {})
    models_map.setdefault(args.model, {})

    target_agent = None
    # Locate the agent entry by id and patch its model field
    for agent in agents_blob.get("list", []):
        if agent.get("id") == args.agent:
            agent["model"] = args.model
            target_agent = agent
            break
    if target_agent is None:
        raise SystemExit(f"Agent '{args.agent}' not found in config")

    write_config(data)
    print(f"Updated primary model to {args.model} (agent={args.agent}). Restart gateway/session to apply.")


def cmd_stop_session(args: argparse.Namespace) -> None:
    """Remove a session entry and its backing files to force a fresh session on next connect."""
    agent_dir = AGENTS_ROOT / args.agent
    sessions_dir = agent_dir / "sessions"
    store_path = sessions_dir / "sessions.json"
    if not store_path.exists():
        raise FileNotFoundError(f"Session store not found at {store_path}")
    store = json.loads(store_path.read_text())
    entry = store.pop(args.key, None)
    if entry is None:
        print(f"Session key {args.key} not found in store")
    else:
        session_file = Path(entry.get("sessionFile", ""))
        if session_file.exists():
            session_file.unlink()
        lock_file = Path(str(session_file) + ".lock")
        if lock_file.exists():
            lock_file.unlink()
        store_path.write_text(json.dumps(store, indent=2) + "\n")
        print(f"Removed session {args.key} (file {session_file.name}).")


def cmd_restart_gateway(_: argparse.Namespace) -> None:
    """Invoke ``openclaw gateway restart`` and relay its output."""
    result = subprocess.run([
        "openclaw",
        "gateway",
        "restart",
    ], capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stdout.write(result.stderr)
    print("Gateway restart command issued.")


def build_parser() -> argparse.ArgumentParser:
    """Construct the argparse CLI with all subcommands and their options."""
    parser = argparse.ArgumentParser(description="Agent control helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Show default + per-agent models")
    p_status.set_defaults(func=cmd_status)

    p_set = sub.add_parser("set-model", help="Update the primary model for an agent and defaults")
    p_set.add_argument("--agent", default="main", help="Agent id to update (default: main)")
    p_set.add_argument("--model", required=True, help="Provider/model identifier, e.g. anthropic/claude-3-opus")
    p_set.add_argument("--fallbacks", help="Comma-separated fallback list to overwrite")
    p_set.set_defaults(func=cmd_set_model)

    p_stop = sub.add_parser("stop-session", help="Remove a stored session entry to force recreation")
    p_stop.add_argument("--agent", default="main", help="Agent id (default: main)")
    p_stop.add_argument("--key", default="agent:main:main", help="Session key to remove")
    p_stop.set_defaults(func=cmd_stop_session)

    p_restart = sub.add_parser("restart-gateway", help="Restart the OpenClaw gateway service")
    p_restart.set_defaults(func=cmd_restart_gateway)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate subcommand handler."""
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
