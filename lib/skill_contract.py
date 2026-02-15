#!/usr/bin/env python3
"""
skill_contract.py — Declarative skill contracts for orchestration.

Each software-development skill declares a contract describing:
- What it can do (capabilities)
- What inputs it needs
- What outputs it produces
- What side effects it has
- What hooks it triggers

The orchestrator reads these contracts to:
1. Route work items to the right skill
2. Validate prerequisites before starting
3. Know what to expect after completion
4. Chain skills into pipelines automatically

Usage:
    from lib.skill_contract import SkillContract, load_contract, list_contracts

    # Skills declare their contract in a JSON file
    contract = load_contract("python-backend")
    print(contract.capabilities)  # ["api_design", "database", "auth", ...]
    print(contract.inputs)        # ["spec", "requirements", "existing_code"]
    print(contract.outputs)       # ["source_files", "tests", "api_docs"]

    # Orchestrator queries
    candidates = find_skills_for(capability="api_design")
    chain = build_pipeline(["spec", "implement", "test", "deploy"])
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

_WORKSPACE = Path(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
CONTRACTS_DIR = _WORKSPACE / "config" / "skill_contracts"


class SkillContract:
    """Declarative contract for a skill's orchestration interface."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def skill_path(self) -> str:
        return self._data.get("skill_path", "")

    @property
    def description(self) -> str:
        return self._data.get("description", "")

    @property
    def capabilities(self) -> List[str]:
        """What this skill can do (tags for routing)."""
        return self._data.get("capabilities", [])

    @property
    def inputs(self) -> List[Dict[str, Any]]:
        """What this skill needs to start work.
        Each input: {"name": str, "type": str, "required": bool, "description": str}
        """
        return self._data.get("inputs", [])

    @property
    def outputs(self) -> List[Dict[str, Any]]:
        """What this skill produces on completion.
        Each output: {"name": str, "type": str, "description": str}
        """
        return self._data.get("outputs", [])

    @property
    def side_effects(self) -> List[str]:
        """External effects (file writes, deployments, API calls)."""
        return self._data.get("side_effects", [])

    @property
    def triggers_hooks(self) -> List[str]:
        """Hook events this skill emits (beyond standard lifecycle)."""
        return self._data.get("triggers_hooks", [])

    @property
    def subscribes_hooks(self) -> List[str]:
        """Hook events this skill listens for (reactive triggers)."""
        return self._data.get("subscribes_hooks", [])

    @property
    def upstream(self) -> List[str]:
        """Skills that typically feed into this one."""
        return self._data.get("upstream", [])

    @property
    def downstream(self) -> List[str]:
        """Skills this one typically feeds into."""
        return self._data.get("downstream", [])

    @property
    def estimated_minutes(self) -> Optional[int]:
        """Typical execution time in minutes."""
        return self._data.get("estimated_minutes")

    @property
    def model_preference(self) -> Optional[str]:
        """Preferred model for this skill's work (alias or full name)."""
        return self._data.get("model_preference")

    def accepts_input(self, input_name: str) -> bool:
        return any(i["name"] == input_name for i in self.inputs)

    def produces_output(self, output_name: str) -> bool:
        return any(o["name"] == output_name for o in self.outputs)

    def has_capability(self, cap: str) -> bool:
        return cap in self.capabilities

    def required_inputs(self) -> List[str]:
        return [i["name"] for i in self.inputs if i.get("required", False)]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"<SkillContract name={self.name!r} caps={self.capabilities}>"


def load_contract(skill_name: str) -> SkillContract:
    """Load a skill contract from config/skill_contracts/<name>.json."""
    path = CONTRACTS_DIR / f"{skill_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No contract found for skill '{skill_name}' at {path}")
    with open(path) as f:
        data = json.load(f)
    return SkillContract(data)


def list_contracts() -> List[SkillContract]:
    """List all registered skill contracts."""
    if not CONTRACTS_DIR.exists():
        return []
    contracts = []
    for f in sorted(CONTRACTS_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            contracts.append(SkillContract(data))
        except Exception:
            continue
    return contracts


def find_skills_for(
    capability: Optional[str] = None,
    input_name: Optional[str] = None,
    output_name: Optional[str] = None,
) -> List[SkillContract]:
    """Find skills matching criteria."""
    results = []
    for c in list_contracts():
        if capability and not c.has_capability(capability):
            continue
        if input_name and not c.accepts_input(input_name):
            continue
        if output_name and not c.produces_output(output_name):
            continue
        results.append(c)
    return results


def build_pipeline(stages: List[str]) -> List[SkillContract]:
    """Given a list of capability stages, find the best skill for each.

    Returns ordered list of contracts, one per stage.
    Raises ValueError if any stage has no matching skill.
    """
    pipeline = []
    for stage in stages:
        candidates = find_skills_for(capability=stage)
        if not candidates:
            raise ValueError(f"No skill found with capability '{stage}'")
        # Prefer the first match (could add scoring later)
        pipeline.append(candidates[0])
    return pipeline
