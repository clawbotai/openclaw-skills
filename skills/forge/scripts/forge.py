#!/usr/bin/env python3
"""
Forge CLI — orchestrate code generation via the Antigravity Forge Daemon.

Usage:
    python3 scripts/forge.py mode1 "build a REST API for webhooks"
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
    classify_error,
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


def _read_skill_files(skill_dir: Path, max_bytes: int = 25000) -> str:
    """Read a skill's key files into a context string."""
    parts = []  # type: List[str]
    total = 0

    # SKILL.md first
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()
        parts.append(f"=== {skill_md.name} ===\n{content}")
        total += len(content)

    # Scripts
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        for f in sorted(scripts_dir.iterdir()):
            if total > max_bytes:
                break
            if f.is_file() and f.suffix in (".py", ".sh", ".js", ".ts"):
                content = f.read_text()
                parts.append(f"=== scripts/{f.name} ===\n{content}")
                total += len(content)

    return "\n\n".join(parts)


def _read_today_memory() -> str:
    """Read today's memory file for usage context."""
    today = time.strftime("%Y-%m-%d")
    mem_file = MEMORY_DIR / f"{today}.md"
    if mem_file.exists():
        content = mem_file.read_text()
        # Truncate to last 3000 chars if huge
        if len(content) > 3000:
            content = "...(truncated)...\n" + content[-3000:]
        return content
    return "(no memory file for today)"


def _spawn_daemon() -> subprocess.Popen:
    """Spawn the forge daemon in stdio mode."""
    if not DAEMON_BIN.exists():
        raise DaemonError(f"Daemon binary not found: {DAEMON_BIN}")

    env = dict(os.environ)
    # Try both env var names
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
        raise JobError(parsed.get("error", "Unknown daemon error"))
    return parsed


def _initialize(proc: subprocess.Popen) -> None:
    """Perform MCP protocol handshake."""
    _send(proc, {
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "forge-cli", "version": "1.0.0"},
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


def run_forge(prompt: str, local_context: str) -> Dict[str, Any]:
    """
    Submit a forge job, poll until complete, return the manifest.

    Raises ForgeError on failure.
    """
    proc = _spawn_daemon()
    try:
        _initialize(proc)

        # Submit
        result = _call_tool(proc, "submit_forge_job", {
            "prompt": prompt,
            "localContext": local_context,
        }, req_id=1)
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

        # Pull manifest
        manifest_resp = _call_tool(proc, "pull_integration_manifest", {
            "jobId": job_id,
        }, req_id=req_id)
        return manifest_resp.get("manifest", manifest_resp)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def build_mode1_prompt(user_prompt: str) -> tuple:
    """Build prompt and context for Mode 1 (code gen)."""
    # Gather workspace tree as context
    context_parts = [f"Workspace: {WORKSPACE}"]

    # Add today's memory for context
    memory = _read_today_memory()
    if memory != "(no memory file for today)":
        context_parts.append(f"Today's context:\n{memory[:2000]}")

    return user_prompt, "\n\n".join(context_parts)


def build_mode2_prompt(operator_name: str, target_name: str) -> tuple:
    """Build prompt and context for Mode 2 (skill × skill)."""
    op_dir = _find_skill_dir(operator_name)
    if not op_dir:
        raise ForgeError(f"Operator skill not found: {operator_name}")

    tgt_dir = _find_skill_dir(target_name)
    if not tgt_dir:
        raise ForgeError(f"Target skill not found: {target_name}")

    operator_content = _read_skill_files(op_dir)
    target_content = _read_skill_files(tgt_dir)
    memory = _read_today_memory()

    prompt = (
        f'Apply the methodology of "{operator_name}" to improve "{target_name}".\n\n'
        f"OPERATOR METHODOLOGY:\n{operator_content}\n\n"
        f"USAGE CONTEXT (today):\n{memory}\n\n"
        "YOUR TASK: Follow the operator's process against the target skill. "
        "Produce concrete file changes — improved SKILL.md, new/updated scripts, fixes. "
        "Do not produce abstract suggestions. Produce actual file content.\n\n"
        "CONSTRAINTS:\n"
        "- Python 3.9 compatible (typing.Optional[X] not X | None)\n"
        "- stdlib-only (no pip dependencies)\n"
        "- No sys.exit() in library functions\n"
        "- Keep scripts under 300 lines\n"
    )

    return prompt, target_content


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage:", file=sys.stderr)
        print("  forge.py mode1 \"prompt text\"", file=sys.stderr)
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
            prompt, context = build_mode1_prompt(" ".join(args))
        elif mode == "mode2":
            if len(args) < 2:
                print("Mode 2 requires: <operator-skill> <target-skill>", file=sys.stderr)
                sys.exit(1)
            prompt, context = build_mode2_prompt(args[0], args[1])
        else:
            print(f"Unknown mode: {mode}. Use mode1 or mode2.", file=sys.stderr)
            sys.exit(1)

        manifest = run_forge(prompt, context)
        elapsed = time.time() - start_time
        log_success(mode, args, elapsed)

        # Output manifest as JSON
        print(json.dumps(manifest, indent=2))

    except Exception as exc:
        elapsed = time.time() - start_time
        log_failure(mode, args, exc, elapsed)
        print(f"[forge] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
