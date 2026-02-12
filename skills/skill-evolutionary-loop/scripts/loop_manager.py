#!/usr/bin/env python3
"""
Evolutionary Loop — Loop Manager
=================================
Orchestrates the Research → Build → Reflect helix.

This script is invoked by the OpenClaw agent to manage build iterations
with backpressure gates. It is NOT a standalone daemon — the agent calls
individual functions and reads the outputs.

Usage (from agent context):
    python3 scripts/loop_manager.py init <project_dir> [--gates test,lint,typecheck,build]
    python3 scripts/loop_manager.py gate <project_dir> <gate_name>
    python3 scripts/loop_manager.py status <project_dir>
    python3 scripts/loop_manager.py iterate <project_dir>
    python3 scripts/loop_manager.py complete <project_dir>
    python3 scripts/loop_manager.py reflect <project_dir>

Exit codes:
    0 = success / gate passed
    1 = gate failed (recoverable)
    2 = fatal error (unrecoverable)
    3 = max retries exceeded → trigger reflection
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_RETRIES_PER_GATE = 3
MAX_ITERATIONS = 20
DEFAULT_GATES = {
    "python": {
        "test": "python -m pytest tests/ -x --tb=short",
        "lint": "ruff check src/",
        "typecheck": "mypy src/ --ignore-missing-imports",
        "build": "python -c 'import importlib; importlib.import_module(\"src\")'",
    },
    "node": {
        "test": "npm run test",
        "lint": "npm run lint",
        "typecheck": "npx tsc --noEmit",
        "build": "npm run build",
    },
    "go": {
        "test": "go test ./...",
        "lint": "golangci-lint run",
        "typecheck": "go vet ./...",
        "build": "go build ./...",
    },
}

STATE_FILE = ".evo-loop-state.json"

# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------

def load_state(project_dir: str) -> dict:
    """Load or create the loop state file."""
    state_path = Path(project_dir) / STATE_FILE
    if state_path.exists():
        with open(state_path) as f:
            return json.load(f)
    return {
        "phase": "init",
        "iteration": 0,
        "max_iterations": MAX_ITERATIONS,
        "gates": {},
        "gate_results": [],
        "started_at": None,
        "completed_at": None,
        "status": "not_started",
        "retries": {},
        "lessons": [],
    }


def save_state(project_dir: str, state: dict) -> None:
    """Persist state to disk."""
    state_path = Path(project_dir) / STATE_FILE
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Gate Execution
# ---------------------------------------------------------------------------

def run_gate(project_dir: str, gate_name: str, command: str) -> dict:
    """
    Execute a single backpressure gate.

    Returns:
        {
            "gate": str,
            "passed": bool,
            "exit_code": int,
            "stdout": str,
            "stderr": str,
            "duration_ms": int
        }
    """
    start = datetime.now(timezone.utc)
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5-minute timeout per gate
        )
        duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return {
            "gate": gate_name,
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
            "duration_ms": duration,
        }
    except subprocess.TimeoutExpired:
        duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return {
            "gate": gate_name,
            "passed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"TIMEOUT: Gate '{gate_name}' exceeded 300s limit",
            "duration_ms": duration,
        }
    except Exception as e:
        return {
            "gate": gate_name,
            "passed": False,
            "exit_code": -2,
            "stdout": "",
            "stderr": f"ERROR: {str(e)}",
            "duration_ms": 0,
        }


def run_all_gates(project_dir: str, gates: dict) -> list:
    """Run all configured gates in sequence. Stop on first failure."""
    results = []
    for name, command in gates.items():
        result = run_gate(project_dir, name, command)
        results.append(result)
        if not result["passed"]:
            break  # Stop at first failure — fix this before continuing
    return results


# ---------------------------------------------------------------------------
# Progress Logging
# ---------------------------------------------------------------------------

def append_progress(project_dir: str, iteration: int, task: str,
                    gate_results: list[dict], retries: int,
                    files_changed: list[str], status: str,
                    next_task: str = "") -> None:
    """Append an iteration entry to PROGRESS.md."""
    progress_path = Path(project_dir) / "PROGRESS.md"
    now = datetime.now(timezone.utc).isoformat()

    gate_lines = []
    for g in gate_results:
        status_emoji = "✅" if g["passed"] else "❌"
        gate_lines.append(f"- {g['gate']}: {status_emoji} ({g['duration_ms']}ms)")
        if not g["passed"] and g["stderr"]:
            # Include first 3 lines of error for context
            err_preview = "\n".join(g["stderr"].strip().split("\n")[:3])
            gate_lines.append(f"  ```\n  {err_preview}\n  ```")

    files_lines = [f"- `{f}`" for f in files_changed] if files_changed else ["- (none)"]

    entry = f"""
## Iteration {iteration} — {now}

### Task
{task}

### Result
{status}

### Gate Results
{chr(10).join(gate_lines)}

### Self-Correction Retries
{retries}

### Files Changed
{chr(10).join(files_lines)}

### Next
{next_task if next_task else "(end of iteration)"}
"""

    with open(progress_path, "a") as f:
        f.write(entry)


def write_completion(project_dir: str, total_iterations: int,
                     files_created: list[str]) -> None:
    """Write the final completion entry to PROGRESS.md."""
    progress_path = Path(project_dir) / "PROGRESS.md"
    now = datetime.now(timezone.utc).isoformat()

    files_lines = [f"- `{f}`" for f in files_created]

    entry = f"""
## Status: COMPLETE ✅

**Finished:** {now}
**Total Iterations:** {total_iterations}

### Files Created/Modified
{chr(10).join(files_lines)}
"""

    with open(progress_path, "a") as f:
        f.write(entry)


def write_blocked(project_dir: str, iteration: int, blocker: str,
                  attempts: list[str]) -> None:
    """Write a BLOCKED status entry to PROGRESS.md."""
    progress_path = Path(project_dir) / "PROGRESS.md"
    now = datetime.now(timezone.utc).isoformat()

    attempts_lines = [f"{i+1}. {a}" for i, a in enumerate(attempts)]

    entry = f"""
## Status: BLOCKED 🛑

**Blocked at:** {now}
**Iteration:** {iteration}

### Blocker
{blocker}

### Attempted Solutions
{chr(10).join(attempts_lines)}

### Action Required
Phase 3 (Reflection) should analyze this failure and extract lessons.
"""

    with open(progress_path, "a") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Reflection Data Collection
# ---------------------------------------------------------------------------

def collect_reflection_data(project_dir: str) -> dict:
    """
    Gather all evidence needed for Phase 3 reflection.

    Returns a structured dict the agent uses to generate the reflection report.
    """
    state = load_state(project_dir)
    project = Path(project_dir)

    # Read SPECIFICATION.md
    spec = ""
    spec_path = project / "SPECIFICATION.md"
    if spec_path.exists():
        spec = spec_path.read_text()[:5000]

    # Read PROGRESS.md
    progress = ""
    progress_path = project / "PROGRESS.md"
    if progress_path.exists():
        progress = progress_path.read_text()[:10000]

    # Read IMPLEMENTATION_PLAN.md
    plan = ""
    plan_path = project / "IMPLEMENTATION_PLAN.md"
    if plan_path.exists():
        plan = plan_path.read_text()[:5000]

    # Count failures
    total_failures = sum(
        1 for r in state.get("gate_results", [])
        if not r.get("passed", True)
    )

    # Identify patterns in failures
    failure_gates = {}
    for r in state.get("gate_results", []):
        if not r.get("passed", True):
            gate = r.get("gate", "unknown")
            failure_gates[gate] = failure_gates.get(gate, 0) + 1

    return {
        "project_dir": project_dir,
        "status": state.get("status", "unknown"),
        "total_iterations": state.get("iteration", 0),
        "max_iterations": state.get("max_iterations", MAX_ITERATIONS),
        "total_gate_failures": total_failures,
        "failure_distribution": failure_gates,
        "specification_excerpt": spec,
        "progress_log": progress,
        "implementation_plan": plan,
        "lessons_already_recorded": state.get("lessons", []),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def init_project(project_dir: str, gate_preset: str = "python",
                 custom_gates: Optional[dict] = None) -> dict:
    """
    Initialize the evolutionary loop for a project directory.

    Creates state file and PROGRESS.md header.
    """
    project = Path(project_dir)
    project.mkdir(parents=True, exist_ok=True)

    gates = custom_gates if custom_gates else DEFAULT_GATES.get(gate_preset, {})

    state = load_state(project_dir)
    state.update({
        "phase": "research",
        "iteration": 0,
        "gates": gates,
        "gate_results": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "initialized",
        "retries": {},
        "lessons": [],
    })
    save_state(project_dir, state)

    # Create PROGRESS.md header
    progress_path = project / "PROGRESS.md"
    if not progress_path.exists():
        progress_path.write_text(
            f"# Evolutionary Loop — Progress Log\n"
            f"*Started: {state['started_at']}*\n"
            f"*Gates: {', '.join(gates.keys())}*\n"
        )

    return state


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def print_json(data: dict) -> None:
    """Print structured output for the agent to parse."""
    print(json.dumps(data, indent=2, default=str))


def main():
    """Handle this operation."""
    if len(sys.argv) < 3:
        print("Usage: loop_manager.py <command> <project_dir> [args...]", file=sys.stderr)
        print("Commands: init, gate, status, iterate, complete, reflect", file=sys.stderr)
        sys.exit(2)

    command = sys.argv[1]
    project_dir = os.path.abspath(sys.argv[2])

    if command == "init":
        preset = "python"
        custom_gates = None
        if len(sys.argv) > 3 and sys.argv[3] == "--gates":
            # Parse custom gates from key=value pairs
            custom_gates = {}
            for pair in sys.argv[4:]:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    custom_gates[k] = v
        elif len(sys.argv) > 3:
            preset = sys.argv[3]
        state = init_project(project_dir, preset, custom_gates)
        print_json({"action": "init", "status": "ok", "state": state})

    elif command == "gate":
        if len(sys.argv) < 4:
            print("Usage: loop_manager.py gate <project_dir> <gate_name>", file=sys.stderr)
            sys.exit(2)
        gate_name = sys.argv[3]
        state = load_state(project_dir)
        gates = state.get("gates", {})
        if gate_name not in gates:
            if gate_name == "all":
                results = run_all_gates(project_dir, gates)
                all_passed = all(r["passed"] for r in results)
                state["gate_results"].extend(results)
                save_state(project_dir, state)
                print_json({"action": "gate_all", "passed": all_passed, "results": results})
                sys.exit(0 if all_passed else 1)
            else:
                print(f"Unknown gate: {gate_name}. Available: {list(gates.keys())}", file=sys.stderr)
                sys.exit(2)
        result = run_gate(project_dir, gate_name, gates[gate_name])
        state["gate_results"].append(result)
        save_state(project_dir, state)
        print_json({"action": "gate", **result})
        sys.exit(0 if result["passed"] else 1)

    elif command == "status":
        state = load_state(project_dir)
        # Summarize gate results
        total_runs = len(state.get("gate_results", []))
        total_pass = sum(1 for r in state.get("gate_results", []) if r.get("passed"))
        print_json({
            "action": "status",
            "phase": state.get("phase"),
            "iteration": state.get("iteration"),
            "status": state.get("status"),
            "gates_configured": list(state.get("gates", {}).keys()),
            "total_gate_runs": total_runs,
            "total_gate_passes": total_pass,
            "total_gate_failures": total_runs - total_pass,
            "started_at": state.get("started_at"),
        })

    elif command == "iterate":
        state = load_state(project_dir)
        state["iteration"] = state.get("iteration", 0) + 1
        state["phase"] = "build"
        state["status"] = "iterating"

        if state["iteration"] > state.get("max_iterations", MAX_ITERATIONS):
            state["status"] = "max_iterations_exceeded"
            save_state(project_dir, state)
            print_json({
                "action": "iterate",
                "status": "max_iterations_exceeded",
                "iteration": state["iteration"],
                "message": "Trigger Phase 3 reflection.",
            })
            sys.exit(3)

        save_state(project_dir, state)
        print_json({
            "action": "iterate",
            "status": "ok",
            "iteration": state["iteration"],
        })

    elif command == "complete":
        state = load_state(project_dir)
        state["phase"] = "reflect"
        state["status"] = "completed"
        state["completed_at"] = datetime.now(timezone.utc).isoformat()
        save_state(project_dir, state)
        print_json({
            "action": "complete",
            "status": "ok",
            "iterations": state["iteration"],
            "message": "Build phase complete. Proceed to Phase 3 reflection.",
        })

    elif command == "reflect":
        data = collect_reflection_data(project_dir)
        state = load_state(project_dir)
        state["phase"] = "reflect"
        save_state(project_dir, state)
        print_json({"action": "reflect", "data": data})

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
