#!/usr/bin/env python3
"""
Forge CLI — orchestrate code generation via the Antigravity Forge Daemon.

GUARDRAIL-AWARE: Sends file PATHS (not content) to the daemon. Reads manifest
from disk (not MCP response). The daemon handles all heavy I/O locally.

Usage:
    python3 scripts/forge.py mode1 "build a REST API for webhooks" path1 path2
    python3 scripts/forge.py mode2 lifecycle forge
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent  # skills/forge/
WORKSPACE = SKILL_DIR.parent.parent  # workspace root
DAEMON_BIN = WORKSPACE / "antigravity-forge-daemon" / "dist" / "index.js"
SKILLS_DIR = WORKSPACE / "skills"
MEMORY_DIR = WORKSPACE / "memory"

# Import monitor
sys.path.insert(0, str(SCRIPT_DIR))
from monitor_wrapper import (
    ForgeError,
    check_circuit_breaker,
    log_failure,
    log_success,
)

POLL_INTERVAL = 5
MAX_POLL_TIME = 300  # 5 minutes


class DaemonError(ForgeError):
    """Error communicating with the forge daemon."""
    pass


class JobError(ForgeError):
    """Forge job failed."""
    pass


def _find_skill_dir(name: str) -> Optional[Path]:
    """Find a skill directory by name (case-insensitive, hyphen-tolerant)."""
    if not SKILLS_DIR.is_dir():
        return None
    normalized = name.lower().replace("_", "-")
    for d in SKILLS_DIR.iterdir():
        if d.is_dir() and d.name.lower().replace("_", "-") == normalized:
            return d
    return None


def _collect_skill_paths(skill_dir: Path) -> List[str]:
    """Collect absolute paths of key files in a skill directory."""
    paths = []  # type: List[str]
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        paths.append(str(skill_md))

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        paths.append(str(scripts_dir))

    # Include SPECIFICATION.md, templates, etc.
    for extra in ["SPECIFICATION.md", "templates", "prompts"]:
        p = skill_dir / extra
        if p.exists():
            paths.append(str(p))

    return paths


def _spawn_daemon() -> subprocess.Popen:
    """Spawn the forge daemon in stdio mode."""
    if not DAEMON_BIN.exists():
        raise DaemonError(f"Daemon binary not found: {DAEMON_BIN}")

    env = dict(os.environ)
    if "GEMINI_API_KEY" not in env:
        google_key = env.get("GOOGLE_API_KEY", "")
        if google_key:
            env["GEMINI_API_KEY"] = google_key
        else:
            raise DaemonError(
                "GEMINI_API_KEY not set. Export it or set GOOGLE_API_KEY."
            )

    proc = subprocess.Popen(
        ["node", str(DAEMON_BIN)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return proc


def _send(proc: subprocess.Popen, msg: Dict[str, Any]) -> None:
    """Send a JSON-RPC message to the daemon."""
    assert proc.stdin is not None
    data = json.dumps(msg) + "\n"
    proc.stdin.write(data.encode())
    proc.stdin.flush()


def _recv(proc: subprocess.Popen) -> Dict[str, Any]:
    """Read a JSON-RPC response from the daemon."""
    assert proc.stdout is not None
    while True:
        line = proc.stdout.readline().decode().strip()
        if not line:
            raise DaemonError("Daemon closed stdout unexpectedly.")
        if line.startswith("{"):
            return json.loads(line)


def _extract_text(resp: Dict[str, Any]) -> Dict[str, Any]:
    """Extract parsed JSON from MCP tool response content."""
    content = resp.get("result", {}).get("content", [])
    if not content:
        raise DaemonError(f"Empty response from daemon: {resp}")
    text = content[0].get("text", "{}")
    parsed = json.loads(text)
    if resp.get("result", {}).get("isError"):
        raise JobError(parsed.get("error", parsed.get("statusMessage", "Unknown daemon error")))
    return parsed


def _initialize(proc: subprocess.Popen) -> None:
    """Perform MCP protocol handshake."""
    _send(proc, {
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "forge-cli", "version": "2.0.0"},
        },
    })
    _recv(proc)  # init response
    _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})


def _call_tool(
    proc: subprocess.Popen,
    tool: str,
    arguments: Dict[str, Any],
    req_id: int = 1,
) -> Dict[str, Any]:
    """Call an MCP tool and return parsed result."""
    _send(proc, {
        "jsonrpc": "2.0", "id": req_id, "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    })
    return _extract_text(_recv(proc))


def run_forge(
    prompt: str,
    target_paths: List[str],
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submit a forge job, poll until complete, return the manifest pointer.

    GUARDRAIL 1: Sends paths, not content.
    GUARDRAIL 2: Returns manifest pointer (reads manifest from disk).

    If workspace_root is provided, the daemon applies all file operations
    (CREATE/UPDATE/DELETE) to that directory automatically.

    Raises ForgeError on failure.
    """
    proc = _spawn_daemon()
    try:
        _initialize(proc)

        # Submit with paths only (GUARDRAIL 1)
        submit_args = {
            "prompt": prompt,
            "targetPaths": target_paths,
        }  # type: Dict[str, Any]
        if workspace_root:
            submit_args["workspaceRoot"] = workspace_root

        result = _call_tool(proc, "submit_forge_job", submit_args, req_id=1)
        job_id = result.get("jobId")
        if not job_id:
            raise JobError(f"No jobId in response: {result}")

        print(f"[forge] Job submitted: {job_id}", file=sys.stderr)

        # Poll
        start = time.time()
        req_id = 2
        while time.time() - start < MAX_POLL_TIME:
            time.sleep(POLL_INTERVAL)
            status = _call_tool(proc, "poll_job_status", {
                "jobId": job_id,
            }, req_id=req_id)
            req_id += 1

            state = status.get("state", "UNKNOWN")
            elapsed = status.get("elapsedSeconds", "?")
            msg = status.get("statusMessage", "")
            print(f"[forge] {state} ({elapsed}s) {msg}", file=sys.stderr)

            if state == "COMPLETED":
                break
            elif state == "FAILED":
                raise JobError(f"Job failed: {msg}")
        else:
            raise JobError(f"Job timed out after {MAX_POLL_TIME}s")

        # Pull manifest pointer (GUARDRAIL 2)
        pointer = _call_tool(proc, "pull_integration_manifest", {
            "jobId": job_id,
        }, req_id=req_id)

        # Read the actual manifest from disk
        manifest_path = pointer.get("manifestPath", "")
        if manifest_path and os.path.exists(manifest_path):
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            return {
                "pointer": pointer,
                "manifest": manifest,
            }
        else:
            # Fallback: return pointer only
            return {"pointer": pointer}

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def build_mode1(args: List[str]) -> tuple:
    """Build prompt, target paths, and workspace root for Mode 1 (code gen).
    Returns (prompt, target_paths, workspace_root).
    """
    if not args:
        raise ForgeError("Mode 1 requires a prompt string.")

    prompt = args[0]
    target_paths = [os.path.abspath(p) for p in args[1:]] if len(args) > 1 else []

    if not target_paths:
        target_paths = [str(WORKSPACE)]

    # workspace_root = first directory in target_paths, or WORKSPACE
    workspace_root = str(WORKSPACE)
    for p in target_paths:
        if os.path.isdir(p):
            workspace_root = p
            break

    return prompt, target_paths, workspace_root


def build_mode2(args: List[str]) -> tuple:
    """Build prompt, target paths, and workspace root for Mode 2 (skill × skill).
    Returns (prompt, target_paths, workspace_root).
    """
    if len(args) < 2:
        raise ForgeError("Mode 2 requires: <operator-skill> <target-skill>")

    operator_name, target_name = args[0], args[1]

    op_dir = _find_skill_dir(operator_name)
    if not op_dir:
        raise ForgeError(f"Operator skill not found: {operator_name}")

    tgt_dir = _find_skill_dir(target_name)
    if not tgt_dir:
        raise ForgeError(f"Target skill not found: {target_name}")

    target_paths = []  # type: List[str]

    # Operator's SKILL.md as context
    op_skill_md = op_dir / "SKILL.md"
    if op_skill_md.exists():
        target_paths.append(str(op_skill_md))

    # Full target skill directory
    target_paths.append(str(tgt_dir))

    # Today's memory for usage context
    today = time.strftime("%Y-%m-%d")
    mem_file = MEMORY_DIR / f"{today}.md"
    if mem_file.exists():
        target_paths.append(str(mem_file))

    prompt = (
        f'Apply the methodology of "{operator_name}" to improve "{target_name}".\n\n'
        f"The operator skill's SKILL.md describes the methodology to follow.\n"
        f"The target skill's files are the subject of improvement.\n"
        f"Today's memory file provides recent usage context.\n\n"
        f"Follow the operator's process against the target skill. "
        f"Produce concrete file changes — improved SKILL.md, new/updated scripts, fixes. "
        f"Do not produce abstract suggestions. Produce actual complete file content.\n\n"
        f"CONSTRAINTS:\n"
        f"- Python 3.9 compatible (typing.Optional[X] not X | None)\n"
        f"- stdlib-only (no pip dependencies)\n"
        f"- No sys.exit() in library functions\n"
        f"- Keep scripts under 300 lines\n"
    )

    # workspace_root = the target skill directory (where files get written)
    workspace_root = str(tgt_dir)

    return prompt, target_paths, workspace_root


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage:", file=sys.stderr)
        print("  forge.py mode1 \"prompt text\" [path1 path2 ...]", file=sys.stderr)
        print("  forge.py mode2 <operator-skill> <target-skill>", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]

    # Circuit breaker check
    breaker_msg = check_circuit_breaker()
    if breaker_msg:
        print(f"[forge] {breaker_msg}", file=sys.stderr)
        sys.exit(2)

    start_time = time.time()
    args = sys.argv[2:]

    try:
        if mode == "mode1":
            prompt, target_paths, workspace_root = build_mode1(args)
        elif mode == "mode2":
            prompt, target_paths, workspace_root = build_mode2(args)
        else:
            print(f"Unknown mode: {mode}. Use mode1 or mode2.", file=sys.stderr)
            sys.exit(1)

        result = run_forge(prompt, target_paths, workspace_root)
        elapsed = time.time() - start_time
        log_success(mode, args, elapsed)

        # Output result as JSON
        print(json.dumps(result, indent=2))

    except Exception as exc:
        elapsed = time.time() - start_time
        log_failure(mode, args, exc, elapsed)
        print(f"[forge] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
