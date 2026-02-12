#!/usr/bin/env python3
"""
skill_pipeline.py — Orchestrates the Skill Factory Pipeline.

Connects skill-scout, skill-lifecycle, and skill-creator-extended into
a unified flow:

  skill-scout (discover/evaluate)
       ↓ score < threshold
  skill-creator-extended (rebuild)
       ↓ new skill generated
  skill-lifecycle (monitor)
       ↓ circuit breaker OPEN
  skill-scout (find replacement)

Usage:
    from lib.skill_pipeline import evaluate_and_improve, monitor_skill

    # Evaluate a skill, rebuild if below threshold
    evaluate_and_improve("skills/my-skill", threshold=60)

    # Register a skill for lifecycle monitoring
    monitor_skill("my-skill", "python3 skills/my-skill/scripts/main.py test")
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

_WORKSPACE = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

# Skill script paths
_SCOUT_EVALUATE = os.path.join(
    _WORKSPACE, "skills", "skill-scout", "scripts", "evaluate.py"
)
_LIFECYCLE_MONITOR = os.path.join(
    _WORKSPACE, "skills", "skill-lifecycle", "scripts", "monitor.py"
)
_LIFECYCLE_RUNNER = os.path.join(
    _WORKSPACE, "skills", "skill-lifecycle", "scripts", "run_monitored.py"
)
_ARCHITECT = os.path.join(
    _WORKSPACE, "skills", "skill-creator-extended", "architect_skill.py"
)


def _run_cmd(
    cmd: List[str], timeout: int = 120, parse_json: bool = True
) -> Any:
    """Run a subprocess and optionally parse JSON output.

    Args:
        cmd: Command and arguments.
        timeout: Max seconds.
        parse_json: If True, parse stdout as JSON.

    Returns:
        Parsed JSON dict, or raw stdout string if parse_json=False.

    Raises:
        RuntimeError: On command failure.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_WORKSPACE,
            env={**os.environ, "OPENCLAW_WORKSPACE": _WORKSPACE},
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out after {timeout}s: {cmd[0]}")
    except FileNotFoundError:
        raise RuntimeError(f"Script not found: {cmd[0]}")

    output = result.stdout.strip()
    if result.returncode != 0 and not output:
        raise RuntimeError(
            f"Command failed (exit {result.returncode}): {result.stderr[:300]}"
        )

    if parse_json and output:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            # Some commands produce non-JSON output
            return {"raw_output": output, "returncode": result.returncode}

    return output


# ---------------------------------------------------------------------------
# Scout → Evaluate
# ---------------------------------------------------------------------------

def evaluate_skill(skill_path: str) -> Dict[str, Any]:
    """Evaluate a skill's quality and security using skill-scout.

    Args:
        skill_path: Path to the skill directory (relative to workspace).

    Returns:
        Dict with score, grade, details from evaluate.py.
    """
    if not os.path.exists(_SCOUT_EVALUATE):
        raise RuntimeError(f"skill-scout evaluate.py not found at {_SCOUT_EVALUATE}")

    return _run_cmd([sys.executable, _SCOUT_EVALUATE, "score", "--path", skill_path])


# ---------------------------------------------------------------------------
# Lifecycle → Monitor
# ---------------------------------------------------------------------------

def monitor_status() -> Dict[str, Any]:
    """Get skill-lifecycle monitor status (all skills).

    Returns:
        Dict with skill health data, circuit breaker states, error counts.
    """
    if not os.path.exists(_LIFECYCLE_MONITOR):
        raise RuntimeError("skill-lifecycle monitor.py not found")

    return _run_cmd([sys.executable, _LIFECYCLE_MONITOR, "status"])


def monitor_tickets() -> Dict[str, Any]:
    """Get pending repair tickets from skill-lifecycle.

    Returns:
        Dict with tickets list.
    """
    return _run_cmd([sys.executable, _LIFECYCLE_MONITOR, "tickets"])


def run_monitored(skill_name: str, command: List[str], timeout: int = 300) -> Dict[str, Any]:
    """Run a command through the skill-lifecycle monitored runner.

    Captures exit code, stderr, and feeds errors into the circuit breaker.

    Args:
        skill_name: Name of the skill being monitored.
        command: The command and arguments to run.
        timeout: Max seconds.

    Returns:
        Dict with exit_code, stdout, stderr, monitoring_result.
    """
    if not os.path.exists(_LIFECYCLE_RUNNER):
        raise RuntimeError("skill-lifecycle run_monitored.py not found")

    cmd = [sys.executable, _LIFECYCLE_RUNNER, skill_name, "--"] + command
    return _run_cmd(cmd, timeout=timeout, parse_json=False)


# ---------------------------------------------------------------------------
# Creator → Generate/Rebuild
# ---------------------------------------------------------------------------

def rebuild_skill(
    skill_name: str,
    description: str,
    output_path: Optional[str] = None,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    """Rebuild a skill using the AI architect.

    Args:
        skill_name: Name for the rebuilt skill.
        description: Detailed prompt describing what the skill should do.
        output_path: Where to create the skill (default: skills/).
        model: OpenAI model to use.

    Returns:
        Dict with generation status and path.
    """
    if not os.path.exists(_ARCHITECT):
        raise RuntimeError("skill-creator-extended architect_skill.py not found")

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set — cannot run architect")

    out = output_path or os.path.join(_WORKSPACE, "skills")
    cmd = [
        sys.executable, _ARCHITECT,
        "--prompt", description,
        "--output-path", out,
        "--model", model,
    ]
    output = _run_cmd(cmd, timeout=300, parse_json=False)
    return {"status": "completed", "output": output, "path": os.path.join(out, skill_name)}


# ---------------------------------------------------------------------------
# Orchestrated Flows
# ---------------------------------------------------------------------------

def evaluate_and_improve(
    skill_path: str,
    threshold: int = 60,
    rebuild_prompt: Optional[str] = None,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    """Evaluate a skill and trigger rebuild if below quality threshold.

    This is the primary orchestrated flow:
    1. Evaluate the skill via skill-scout
    2. If score >= threshold, return the evaluation
    3. If score < threshold, trigger skill-creator-extended to rebuild

    Args:
        skill_path: Path to the skill directory.
        threshold: Minimum acceptable score (0-100).
        rebuild_prompt: Custom prompt for rebuilding. If None, auto-generates
            from the skill's SKILL.md description.
        model: OpenAI model for rebuilding.

    Returns:
        Dict with evaluation results and optional rebuild status.
    """
    # Step 1: Evaluate
    try:
        evaluation = evaluate_skill(skill_path)
    except RuntimeError as exc:
        return {"status": "evaluation_failed", "error": str(exc)}

    score = evaluation.get("score", evaluation.get("total_score", 0))
    skill_name = os.path.basename(skill_path)

    result = {
        "skill": skill_name,
        "score": score,
        "threshold": threshold,
        "evaluation": evaluation,
    }

    if score >= threshold:
        result["status"] = "passed"
        result["action"] = "none"
        return result

    # Step 2: Score below threshold — attempt rebuild
    result["status"] = "below_threshold"
    result["action"] = "rebuild_triggered"

    if not rebuild_prompt:
        # Auto-generate prompt from SKILL.md
        skill_md = os.path.join(skill_path, "SKILL.md")
        if os.path.exists(skill_md):
            with open(skill_md, "r") as f:
                content = f.read()
            # Extract description from frontmatter
            if "description:" in content:
                desc_start = content.index("description:") + len("description:")
                desc_end = content.find("\n---", desc_start)
                if desc_end == -1:
                    desc_end = desc_start + 500
                rebuild_prompt = content[desc_start:desc_end].strip().strip("'\"")
            else:
                rebuild_prompt = f"Rebuild the {skill_name} skill with improved quality"
        else:
            rebuild_prompt = f"Build a skill called {skill_name}"

    try:
        rebuild_result = rebuild_skill(skill_name, rebuild_prompt, model=model)
        result["rebuild"] = rebuild_result
    except RuntimeError as exc:
        result["rebuild"] = {"status": "failed", "error": str(exc)}

    return result


def check_and_replace_broken(model: str = "gpt-4o") -> List[Dict[str, Any]]:
    """Check all monitored skills for circuit breaker OPEN and find replacements.

    Flow:
    1. Get skill-lifecycle status
    2. For any skill with circuit breaker OPEN, search for alternatives via skill-scout
    3. Return recommendations

    Args:
        model: OpenAI model for potential rebuilds.

    Returns:
        List of dicts with broken skill info and recommendations.
    """
    try:
        status = monitor_status()
    except RuntimeError:
        return [{"status": "monitor_unavailable"}]

    recommendations = []  # type: List[Dict[str, Any]]

    # Look for skills with OPEN circuit breakers
    skills_data = status.get("skills", {})
    for skill_name, skill_info in skills_data.items():
        cb_state = skill_info.get("circuit_breaker", {}).get("state", "CLOSED")
        if cb_state == "OPEN":
            error_count = skill_info.get("error_count", 0)
            last_error = skill_info.get("last_error", "unknown")

            recommendations.append({
                "skill": skill_name,
                "circuit_breaker": "OPEN",
                "error_count": error_count,
                "last_error": last_error,
                "recommendation": "rebuild_or_replace",
                "action": f"Run: evaluate_and_improve('skills/{skill_name}')",
            })

    return recommendations
