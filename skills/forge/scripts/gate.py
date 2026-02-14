#!/usr/bin/env python3
"""
Backpressure gates for the Forge skill.
Enforces quality standards: Syntax -> Static Analysis -> Tests.

Usage:
    python3 scripts/gate.py [project_root]
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def _run_command(cmd: List[str], cwd: Path, desc: str) -> bool:
    """Run a subprocess command and return True if successful."""
    print(f"[gate] Running {desc}...")
    try:
        # capture_output=False to show output to user
        result = subprocess.run(cmd, cwd=str(cwd), check=False)
        if result.returncode == 0:
            print(f"[gate] {desc}: PASS")
            return True
        else:
            print(f"[gate] {desc}: FAIL (exit code {result.returncode})")
            return False
    except FileNotFoundError:
        print(f"[gate] {desc}: SKIPPED (tool not found: {cmd[0]})")
        return False
    except Exception as e:
        print(f"[gate] {desc}: ERROR ({e})")
        return False


def check_syntax(root: Path) -> bool:
    """Gate 1: Syntax check using compileall."""
    # -q: quiet, -x: regex to exclude (optional)
    # We check the whole root, excluding hidden dirs/venvs usually handled by ignore patterns,
    # but compileall is simple. We'll just run on the root.
    cmd = [sys.executable, "-m", "compileall", "-q", "."]
    return _run_command(cmd, root, "Gate 1: Syntax Check")


def check_static_analysis(root: Path) -> bool:
    """Gate 2: Static Analysis (ruff, flake8, mypy)."""
    passed = True
    tools_found = 0

    # Check for Ruff
    if shutil.which("ruff"):
        tools_found += 1
        if not _run_command(["ruff", "check", "."], root, "Gate 2a: Lint (ruff)"):
            passed = False
    
    # Check for Flake8 (if ruff not found or as additional check)
    elif shutil.which("flake8"):
        tools_found += 1
        if not _run_command(["flake8", "."], root, "Gate 2a: Lint (flake8)"):
            passed = False

    # Check for Mypy
    if shutil.which("mypy"):
        tools_found += 1
        # --ignore-missing-imports is often needed for quick checks in new envs
        if not _run_command(["mypy", ".", "--ignore-missing-imports"], root, "Gate 2b: Typecheck (mypy)"):
            passed = False

    if tools_found == 0:
        print("[gate] Gate 2: Static Analysis SKIPPED (no linters found)")
        # Warning only, doesn't fail the gate if tools are missing, unless strictness is required.
        # Requirement says: "run if available, warn if not".
        print("       WARN: Install ruff/flake8 or mypy for better safety.")
    
    return passed


def check_tests(root: Path) -> bool:
    """Gate 3: Test execution."""
    tests_dir = root / "tests"
    if not tests_dir.exists() or not tests_dir.is_dir():
        print("[gate] Gate 3: Tests SKIPPED (no 'tests' directory)")
        return True

    # Prefer pytest
    if shutil.which("pytest"):
        return _run_command(["pytest"], root, "Gate 3: Tests (pytest)")
    
    # Fallback to unittest
    print("[gate] pytest not found, falling back to unittest...")
    return _run_command([sys.executable, "-m", "unittest", "discover", "tests"], root, "Gate 3: Tests (unittest)")


def run_gates(root: Path) -> bool:
    """Execute all gates in sequence. Stop on first failure."""
    print(f"[gate] Scanning: {root}")
    
    if not check_syntax(root):
        return False
    
    if not check_static_analysis(root):
        return False
    
    if not check_tests(root):
        return False
    
    print("[gate] ALL GATES PASSED \u2705")
    return True


def main() -> None:
    args = sys.argv[1:]
    target_dir = Path(args[0]) if args else Path.cwd()
    
    if not target_dir.exists():
        print(f"Error: Target directory '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    success = run_gates(target_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
