"""Tests for the AuditLog system."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Generator

import pytest

from src.audit import AuditLog


@pytest.fixture
def clean_cwd(tmp_path: Path) -> Generator[Path, None, None]:
    """Run test in a temporary directory to capture audit logs."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


def test_audit_lifecycle(clean_cwd: Path) -> None:
    """Verify full audit lifecycle from transition to failure to finalize."""
    log = AuditLog()
    log.record_state_transition("DRESSED", "PEEPING")
    log.record_failure(
        error_type="DeterministicError",
        message="Anatomy mismatch",
        context={"expected": "Darwin", "got": "Linux"}
    )

    # Finalize writes to the current working directory (clean_cwd)
    log_path_str = log.finalize("ABORTED")
    log_path = Path(log_path_str)

    assert log_path.exists()
    assert log_path.parent == clean_cwd

    content = json.loads(log_path.read_text(encoding="utf-8"))
    assert content["final_state"] == "ABORTED"
    assert len(content["events"]) == 2

    # Verify state transition
    transition = content["events"][0]
    assert transition["type"] == "state_transition"
    assert transition["from"] == "DRESSED"
    assert transition["to"] == "PEEPING"

    # Verify failure record
    failure = content["events"][1]
    assert failure["type"] == "failure"
    assert failure["error_type"] == "DeterministicError"
    assert failure["message"] == "Anatomy mismatch"
    assert failure["context"] == {"expected": "Darwin", "got": "Linux"}
