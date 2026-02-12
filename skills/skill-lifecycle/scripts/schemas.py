"""
Skill Runtime Monitor — Pydantic Schemas
==========================================
Strict-typed data models for the entire monitoring pipeline.

Models:
    ErrorLog          — Single error occurrence (deduplicated via fingerprint)
    SkillHealth       — Aggregated health metrics for one skill
    CircuitState      — Circuit breaker state machine
    RepairTicket      — LLM-optimized payload for the Evolutionary Loop
    ReliabilityReport — Cross-skill analytics summary
    MonitorConfig     — Runtime configuration with sensible defaults
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

# --- Class definition ---
class ErrorClass(str, Enum):
    """
    Two-class error taxonomy optimized for autonomous remediation.

    TRANSIENT errors are environmental — network timeouts, API rate limits,
    temporary unavailability. Retrying usually fixes them. Code changes won't help.

    DETERMINISTIC errors are logic failures — type errors, validation failures,
    incorrect assumptions. These ALWAYS fail for the same input. Only code
    changes fix them. These are what the Evolutionary Loop needs.
    """
    TRANSIENT = "transient"
    DETERMINISTIC = "deterministic"


# --- Class definition ---
class CircuitBreakerState(str, Enum):
    """
    Three-state circuit breaker (Nygard, "Release It!" pattern):

    CLOSED   — Normal operation. Failures are counted.
    OPEN     — Skill quarantined. Calls rejected immediately to save tokens.
    HALF_OPEN — Probe state. One call allowed to test recovery.
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# --- Class definition ---
class TicketPriority(str, Enum):
    """Repair urgency for the Evolutionary Loop."""
    CRITICAL = "critical"   # Skill completely broken, 100% failure rate
    HIGH = "high"           # >50% failure rate or circuit breaker tripped
    MEDIUM = "medium"       # Recurring deterministic error
    LOW = "low"             # Infrequent or transient-only errors


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

# --- Class definition ---
class ErrorLog(BaseModel):
    """
    A single deduplicated error entry.

    Instead of storing every occurrence, errors are fingerprinted by their
    normalized traceback + error message. Identical errors increment a counter
    and update the `last_seen` timestamp. This keeps the ledger compact —
    50 identical failures = 1 entry with count=50.
    """
    fingerprint: str = Field(
        description="SHA-256 hash of normalized error signature"
    )
    skill_name: str = Field(
        description="Canonical skill identifier"
    )
    error_class: ErrorClass = Field(
        description="Transient (retry) vs deterministic (fix code)"
    )
    error_type: str = Field(
        description="Exception class name (e.g., 'KeyError', 'TimeoutError')"
    )
    error_message: str = Field(
        description="The actual error text"
    )
    traceback: str = Field(
        default="",
        description="Full traceback if available"
    )
    input_args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments that triggered the failure — critical for reproduction"
    )
    environment: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment state at failure time (cwd, python version, etc.)"
    )
    count: int = Field(
        default=1,
        description="Number of occurrences of this exact fingerprint"
    )
    first_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    exit_code: Optional[int] = Field(
        default=None,
        description="Process exit code for subprocess-based skills"
    )

    @staticmethod
    def generate_fingerprint(
        skill_name: str,
        error_type: str,
        error_message: str,
        traceback: str = ""
    ) -> str:
        """
        Create a stable fingerprint from the error's identity.

        Normalizes line numbers and memory addresses out of tracebacks
        so that the same logical error always produces the same hash,
        even if it occurs at different line numbers after a code edit.
        """
        import re
        # Strip line numbers, memory addresses, timestamps
        normalized_tb = re.sub(r'line \d+', 'line N', traceback)
        normalized_tb = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', normalized_tb)
        normalized_msg = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', 'TIMESTAMP', error_message)

        raw = f"{skill_name}|{error_type}|{normalized_msg}|{normalized_tb}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class CircuitState(BaseModel):
    """
    Per-skill circuit breaker state.

    When a skill fails `fail_threshold` times within `window_seconds`,
    the circuit OPENS and the skill is quarantined. After `cooldown_seconds`,
    it transitions to HALF_OPEN for a single probe call.
    """
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    half_open_at: Optional[datetime] = None
    probe_success: Optional[bool] = None


class SkillHealth(BaseModel):
    """
    Aggregated health metrics for a single skill.

    This is the "dashboard view" — everything you need to know about
    a skill's reliability at a glance.
    """
    skill_name: str
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    transient_errors: int = 0
    deterministic_errors: int = 0
    circuit: CircuitState = Field(default_factory=CircuitState)
    errors: List[ErrorLog] = Field(default_factory=list)
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

    @computed_field
    @property
    def failure_rate(self) -> float:
        """Failure rate as a percentage (0.0 - 100.0)."""
        if self.total_calls == 0:
            return 0.0
        return round((self.total_failures / self.total_calls) * 100, 2)

    @computed_field
    @property
    def is_quarantined(self) -> bool:
        """True if circuit breaker is OPEN."""
        return self.circuit.state == CircuitBreakerState.OPEN


class RepairTicket(BaseModel):
    """
    LLM-optimized repair payload for the Evolutionary Loop.

    This is the bridge between monitoring and self-healing. It contains
    everything an LLM needs to understand and fix a broken skill:
    the error, the input that caused it, how often it happens, and
    (if available) the source code of the failing skill.

    Designed to be fed directly into skill-evolutionary-loop Phase 3.
    """
    ticket_id: str = Field(
        description="Unique ticket identifier (fingerprint + timestamp)"
    )
    priority: TicketPriority
    skill_name: str
    skill_path: Optional[str] = Field(
        default=None,
        description="Filesystem path to the skill's source code"
    )
    skill_source: Optional[str] = Field(
        default=None,
        description="Source code of the failing skill (for LLM context)"
    )
    error_summary: str = Field(
        description="Human-readable one-line summary of the failure"
    )
    error_class: ErrorClass
    error_type: str
    error_message: str
    traceback: str = ""
    failing_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="The exact arguments that reproduce this failure"
    )
    occurrence_count: int = Field(
        description="How many times this exact error has occurred"
    )
    first_seen: datetime
    last_seen: datetime
    failure_rate: float = Field(
        description="Skill-wide failure rate as percentage"
    )
    suggested_fix_approach: Optional[str] = Field(
        default=None,
        description="Monitor's best guess at fix category"
    )
    related_errors: List[str] = Field(
        default_factory=list,
        description="Fingerprints of potentially related errors"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_llm_prompt(self) -> str:
        """
        Format this ticket as a prompt section for an LLM repair agent.

        This is the key output — optimized for an AI to read, understand,
        and generate a fix.
        """
        source_section = ""
        if self.skill_source:
            source_section = f"""
## Source Code of Failing Skill
```python
{self.skill_source}
```
"""
        input_section = ""
        if self.failing_input:
            import json
            input_section = f"""
## Failing Input (Reproduction Arguments)
```json
{json.dumps(self.failing_input, indent=2, default=str)}
```
"""
        return f"""# Repair Ticket: {self.ticket_id}
**Priority:** {self.priority.value.upper()}
**Skill:** {self.skill_name}
**Error Class:** {self.error_class.value} ({"retry won't help — code must change" if self.error_class == ErrorClass.DETERMINISTIC else "may resolve on retry"})

## Error
**Type:** {self.error_type}
**Message:** {self.error_message}
**Occurrences:** {self.occurrence_count}x (first: {self.first_seen.isoformat()}, last: {self.last_seen.isoformat()})
**Skill Failure Rate:** {self.failure_rate}%

## Traceback
```
{self.traceback}
```
{source_section}{input_section}
## Suggested Approach
{self.suggested_fix_approach or "Analyze the traceback and input to determine root cause."}

## Instructions
Fix the root cause of this error. The fix must:
1. Handle the specific input case that triggers the failure
2. Not break existing functionality
3. Include a test that reproduces and validates the fix
"""


class ReliabilityReport(BaseModel):
    """
    Cross-skill analytics summary.

    Generated on demand to give the agent a bird's-eye view
    of which skills are healthy, which are degraded, and which
    need immediate attention.
    """
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    total_skills_monitored: int = 0
    healthy_skills: int = 0
    degraded_skills: int = 0
    quarantined_skills: int = 0
    skill_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    top_offenders: List[Dict[str, Any]] = Field(default_factory=list)
    velocity_alerts: List[str] = Field(default_factory=list)
    repair_tickets_pending: int = 0

    def to_summary(self) -> str:
        """Human/agent-readable summary string."""
        lines = [
            f"# Skill Reliability Report — {self.generated_at.isoformat()}",
            "",
            f"**Skills Monitored:** {self.total_skills_monitored}",
            f"**Healthy:** {self.healthy_skills} | "
            f"**Degraded:** {self.degraded_skills} | "
            f"**Quarantined:** {self.quarantined_skills}",
            f"**Pending Repair Tickets:** {self.repair_tickets_pending}",
        ]
        if self.velocity_alerts:
            lines.append("\n## ⚠️ Velocity Alerts")
            for alert in self.velocity_alerts:
                lines.append(f"- {alert}")
        if self.top_offenders:
            lines.append("\n## Top Offenders")
            for o in self.top_offenders:
                lines.append(
                    f"- **{o['skill']}**: {o['failure_rate']}% failure rate "
                    f"({o['deterministic_errors']} deterministic errors)"
                )
        return "\n".join(lines)


class MonitorConfig(BaseModel):
    """
    Runtime configuration with production-safe defaults.

    All thresholds are tunable per deployment. The defaults are
    optimized for an autonomous AI agent that pays per API call —
    aggressive circuit breaking to prevent token waste.
    """
    # Circuit breaker
    fail_threshold: int = Field(
        default=5,
        description="Failures before circuit opens"
    )
    window_seconds: int = Field(
        default=300,
        description="Time window for counting failures (5 min)"
    )
    cooldown_seconds: int = Field(
        default=600,
        description="Time before OPEN → HALF_OPEN (10 min)"
    )

    # Ledger management
    max_errors_per_skill: int = Field(
        default=100,
        description="Rolling window: max error entries per skill"
    )
    retention_days: int = Field(
        default=7,
        description="Errors older than this are pruned"
    )
    ledger_path: str = Field(
        default="memory/skill-errors.json",
        description="Path to the persistent error ledger"
    )

    # Repair ticket thresholds
    auto_ticket_threshold: int = Field(
        default=3,
        description="Deterministic error count to auto-generate a repair ticket"
    )
    quarantine_ticket: bool = Field(
        default=True,
        description="Auto-generate CRITICAL ticket when circuit opens"
    )
