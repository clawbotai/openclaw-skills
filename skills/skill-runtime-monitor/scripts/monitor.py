"""
Skill Runtime Monitor — Core Engine
=====================================
The observability layer between an AI agent and its skills/tools.

Four modules in one file (clean architecture, single deployment unit):

1. **Monitor (Interceptor)** — @monitor_skill decorator wraps execution,
   captures context on failure, classifies errors, enforces circuit breaker.

2. **Aggregator (Ledger)** — Persistent JSON database with fingerprint
   deduplication, rolling window cleanup, thread-safe I/O.

3. **Analyst (Surfacing)** — Reliability reports, velocity tracking,
   argument correlation, cross-skill analytics.

4. **Bridge (Feed Reflection)** — Exports LLM-optimized RepairTickets
   for the skill-evolutionary-loop Phase 3.

Usage:
    from monitor import SkillMonitor, monitor_skill

    monitor = SkillMonitor()  # Uses default config

    @monitor_skill(monitor)
    def my_skill(arg1, arg2):
        """Handle this operation."""
        ...

    # Or wrap any callable at runtime:
    result = monitor.execute("skill-name", some_function, args, kwargs)

    # Get analytics:
    report = monitor.generate_reliability_report()

    # Export repair tickets:
    tickets = monitor.export_for_evolution()

CLI:
    python monitor.py status                    # Print reliability report
    python monitor.py tickets                   # Print pending repair tickets
    python monitor.py health <skill_name>       # Health for one skill
    python monitor.py prune                     # Clean up old entries
    python monitor.py export [--output FILE]    # Export tickets as JSON
"""

from __future__ import annotations

import functools
import json
import os
import platform
import subprocess
import sys
import threading
import traceback as tb_module
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from schemas import (
    CircuitBreakerState,
    CircuitState,
    ErrorClass,
    ErrorLog,
    MonitorConfig,
    ReliabilityReport,
    RepairTicket,
    SkillHealth,
    TicketPriority,
)


# ---------------------------------------------------------------------------
# Error Classification Engine
# ---------------------------------------------------------------------------

# Patterns that indicate transient (environmental) errors
TRANSIENT_PATTERNS = [
    # Network
    "timeout", "timed out", "connection refused", "connection reset",
    "connection aborted", "broken pipe", "network unreachable",
    "name resolution", "dns", "ssl", "certificate",
    # HTTP status codes
    "429", "502", "503", "504", "rate limit", "too many requests",
    "service unavailable", "bad gateway", "gateway timeout",
    # Resource
    "out of memory", "oom", "disk full", "no space left",
    "resource temporarily unavailable", "quota exceeded",
    # Process
    "killed", "sigterm", "sigkill",
]

# Patterns that indicate deterministic (logic) errors
DETERMINISTIC_PATTERNS = [
    # Python type/value errors
    "typeerror", "valueerror", "keyerror", "indexerror",
    "attributeerror", "nameerror", "importerror", "modulenotfounderror",
    "syntaxerror", "indentationerror", "zerodivisionerror",
    # Validation
    "validation error", "schema", "pydantic", "invalid",
    "assertion", "assertionerror",
    # Logic
    "not found", "does not exist", "permission denied",
    "unauthorized", "forbidden",
]


def classify_error(
    error_type: str,
    error_message: str,
    traceback_str: str = "",
    exit_code: Optional[int] = None,
) -> ErrorClass:
    """
    Classify an error as transient or deterministic.

    Strategy: Score both categories. If transient signals dominate,
    it's transient. If deterministic signals dominate (or it's ambiguous),
    default to deterministic — it's safer to investigate than to ignore.

    Exit codes:
        - Signal kills (137=OOM, 143=SIGTERM) → transient
        - All others → deterministic
    """
    text = f"{error_type} {error_message} {traceback_str}".lower()

    transient_score = sum(1 for p in TRANSIENT_PATTERNS if p in text)
    deterministic_score = sum(1 for p in DETERMINISTIC_PATTERNS if p in text)

    # Signal-based exit codes are almost always transient
    if exit_code is not None:
        if exit_code in (137, 143, -9, -15):
            transient_score += 3
        elif exit_code != 0:
            deterministic_score += 1

    # Bias toward deterministic — false negatives (missing a real bug)
    # are more expensive than false positives (investigating a transient)
    if transient_score > deterministic_score + 1:
        return ErrorClass.TRANSIENT
    return ErrorClass.DETERMINISTIC


def capture_environment() -> Dict[str, str]:
    """Capture environment state at the moment of failure."""
    return {
        "cwd": os.getcwd(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "user": os.getenv("USER", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Module 1: The Monitor (Interceptor)
# ---------------------------------------------------------------------------

class SkillMonitor:
    """
    Central monitoring engine. Thread-safe, persistent, self-maintaining.

    Responsibilities:
    - Wrap skill executions and catch failures
    - Maintain per-skill circuit breaker state
    - Persist deduplicated errors to disk
    - Generate analytics and repair tickets

    Thread safety: All ledger I/O is protected by a threading.Lock.
    Multiple agent threads can call monitored skills concurrently.
    """

    def __init__(self, config: Optional[MonitorConfig] = None, workspace: Optional[str] = None):
        """Handle this operation."""
        self.config = config or MonitorConfig()
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.ledger_path = self.workspace / self.config.ledger_path
        self._lock = threading.Lock()
        self._health_cache: Dict[str, SkillHealth] = {}

        # Load existing ledger
        self._load_ledger()

    # -------------------------------------------------------------------
    # Ledger I/O (Module 2: Aggregator)
    # -------------------------------------------------------------------

    def _load_ledger(self) -> None:
        """Load the persistent ledger from disk into memory."""
        with self._lock:
            if self.ledger_path.exists():
                try:
                    raw = json.loads(self.ledger_path.read_text())
                    for skill_name, data in raw.items():
                        health = SkillHealth(skill_name=skill_name)
                        health.total_calls = data.get("total_calls", 0)
                        health.total_failures = data.get("total_failures", 0)
                        health.total_successes = data.get("total_successes", 0)
                        health.transient_errors = data.get("transient_errors", 0)
                        health.deterministic_errors = data.get("deterministic_errors", 0)

                        if data.get("last_success"):
                            health.last_success = datetime.fromisoformat(data["last_success"])
                        if data.get("last_failure"):
                            health.last_failure = datetime.fromisoformat(data["last_failure"])

                        # Restore circuit state
                        if "circuit" in data:
                            health.circuit = CircuitState(**data["circuit"])

                        # Restore error logs
                        for e in data.get("errors", []):
                            health.errors.append(ErrorLog(**e))

                        self._health_cache[skill_name] = health
                except (json.JSONDecodeError, Exception):
                    # Corrupted ledger — start fresh but don't lose the file
                    backup = self.ledger_path.with_suffix(".json.bak")
                    self.ledger_path.rename(backup)
                    self._health_cache = {}

    def _save_ledger(self) -> None:
        """Persist the in-memory state to disk. Must be called under lock."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        output = {}
        for skill_name, health in self._health_cache.items():
            output[skill_name] = {
                "total_calls": health.total_calls,
                "total_failures": health.total_failures,
                "total_successes": health.total_successes,
                "transient_errors": health.transient_errors,
                "deterministic_errors": health.deterministic_errors,
                "last_success": health.last_success.isoformat() if health.last_success else None,
                "last_failure": health.last_failure.isoformat() if health.last_failure else None,
                "circuit": health.circuit.model_dump(mode="json"),
                "errors": [e.model_dump(mode="json") for e in health.errors],
            }

        self.ledger_path.write_text(json.dumps(output, indent=2, default=str))

    def _get_health(self, skill_name: str) -> SkillHealth:
        """Get or create health record for a skill."""
        if skill_name not in self._health_cache:
            self._health_cache[skill_name] = SkillHealth(skill_name=skill_name)
        return self._health_cache[skill_name]

    # -------------------------------------------------------------------
    # Circuit Breaker
    # -------------------------------------------------------------------

    def _check_circuit(self, skill_name: str) -> Tuple[bool, str]:
        """
        Check if a skill call should proceed.

        Returns:
            (allowed: bool, reason: str)
        """
        health = self._get_health(skill_name)
        circuit = health.circuit
        now = datetime.now(timezone.utc)

        if circuit.state == CircuitBreakerState.CLOSED:
            return True, "circuit closed"

        if circuit.state == CircuitBreakerState.OPEN:
            if circuit.opened_at:
                elapsed = (now - circuit.opened_at).total_seconds()
                if elapsed >= self.config.cooldown_seconds:
                    circuit.state = CircuitBreakerState.HALF_OPEN
                    circuit.half_open_at = now
                    return True, "circuit half-open (probe)"
            return False, (
                f"QUARANTINED: {skill_name} circuit is OPEN. "
                f"Failed {circuit.failure_count}x. "
                f"Cooldown expires in "
                f"{self.config.cooldown_seconds - int((now - circuit.opened_at).total_seconds())}s."
            )

        if circuit.state == CircuitBreakerState.HALF_OPEN:
            # Only one probe allowed
            if circuit.probe_success is None:
                return True, "circuit half-open (probe in progress)"
            return False, "circuit half-open (probe already in progress)"

        return True, "unknown state — allowing"

    def _record_success(self, skill_name: str) -> None:
        """Record a successful call. Resets circuit breaker if needed."""
        health = self._get_health(skill_name)
        health.total_calls += 1
        health.total_successes += 1
        health.last_success = datetime.now(timezone.utc)

        if health.circuit.state == CircuitBreakerState.HALF_OPEN:
            # Probe succeeded — close circuit
            health.circuit.state = CircuitBreakerState.CLOSED
            health.circuit.failure_count = 0
            health.circuit.probe_success = True

    def _record_failure(
        self,
        skill_name: str,
        error_type: str,
        error_message: str,
        traceback_str: str,
        input_args: Dict[str, Any],
        exit_code: Optional[int] = None,
    ) -> ErrorLog:
        """
        Record a failure. Updates health, circuit breaker, and error ledger.
        Returns the ErrorLog entry (new or updated).
        """
        now = datetime.now(timezone.utc)
        health = self._get_health(skill_name)
        health.total_calls += 1
        health.total_failures += 1
        health.last_failure = now

        # Classify
        error_class = classify_error(error_type, error_message, traceback_str, exit_code)
        if error_class == ErrorClass.TRANSIENT:
            health.transient_errors += 1
        else:
            health.deterministic_errors += 1

        # Fingerprint and deduplicate
        fingerprint = ErrorLog.generate_fingerprint(
            skill_name, error_type, error_message, traceback_str
        )
        existing = next((e for e in health.errors if e.fingerprint == fingerprint), None)

        if existing:
            existing.count += 1
            existing.last_seen = now
            # Update input_args if this is a new variation
            if input_args and input_args != existing.input_args:
                existing.input_args = input_args
            error_log = existing
        else:
            error_log = ErrorLog(
                fingerprint=fingerprint,
                skill_name=skill_name,
                error_class=error_class,
                error_type=error_type,
                error_message=error_message,
                traceback=traceback_str,
                input_args=input_args,
                environment=capture_environment(),
                exit_code=exit_code,
                first_seen=now,
                last_seen=now,
            )
            health.errors.append(error_log)

        # Circuit breaker logic
        circuit = health.circuit
        if circuit.state == CircuitBreakerState.HALF_OPEN:
            # Probe failed — reopen
            circuit.state = CircuitBreakerState.OPEN
            circuit.opened_at = now
            circuit.probe_success = False
        elif circuit.state == CircuitBreakerState.CLOSED:
            # Count failures within window
            window_start = now - timedelta(seconds=self.config.window_seconds)
            recent_failures = sum(
                e.count for e in health.errors
                if e.last_seen >= window_start
            )
            circuit.failure_count = recent_failures
            if recent_failures >= self.config.fail_threshold:
                circuit.state = CircuitBreakerState.OPEN
                circuit.opened_at = now

        # Prune old errors (rolling window)
        self._prune_errors(health)

        return error_log

    def _prune_errors(self, health: SkillHealth) -> None:
        """Remove old errors beyond retention window and count limit."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)

        # Remove expired
        health.errors = [e for e in health.errors if e.last_seen >= cutoff]

        # Enforce max count — keep most recent
        if len(health.errors) > self.config.max_errors_per_skill:
            health.errors.sort(key=lambda e: e.last_seen, reverse=True)
            health.errors = health.errors[:self.config.max_errors_per_skill]

    # -------------------------------------------------------------------
    # Public API: Execute & Monitor
    # -------------------------------------------------------------------

    def execute(
        self,
        skill_name: str,
        fn: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a skill function with full monitoring.

        Checks circuit breaker, captures context on failure,
        classifies errors, updates ledger.

        Raises:
            RuntimeError: If skill is quarantined (circuit OPEN)
            Original exception: Re-raised after logging
        """
        kwargs = kwargs or {}

        with self._lock:
            allowed, reason = self._check_circuit(skill_name)
            if not allowed:
                raise RuntimeError(reason)

        # Capture input args for context
        input_context = {}
        try:
            import inspect
            sig = inspect.signature(fn)
            param_names = list(sig.parameters.keys())
            for i, arg in enumerate(args):
                name = param_names[i] if i < len(param_names) else f"arg_{i}"
                input_context[name] = _safe_repr(arg)
            for k, v in kwargs.items():
                input_context[k] = _safe_repr(v)
        except Exception:
            input_context = {"raw_args": str(args)[:500], "raw_kwargs": str(kwargs)[:500]}

        try:
            result = fn(*args, **kwargs)

            with self._lock:
                self._record_success(skill_name)
                self._save_ledger()

            return result

        except Exception as exc:
            error_type = type(exc).__name__
            error_message = str(exc)
            traceback_str = tb_module.format_exc()

            with self._lock:
                error_log = self._record_failure(
                    skill_name=skill_name,
                    error_type=error_type,
                    error_message=error_message,
                    traceback_str=traceback_str,
                    input_args=input_context,
                )
                self._save_ledger()

            raise

    def execute_subprocess(
        self,
        skill_name: str,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """
        Execute a subprocess-based skill with monitoring.

        For skills that are shell scripts or external tools
        rather than Python functions.
        """
        with self._lock:
            allowed, reason = self._check_circuit(skill_name)
            if not allowed:
                raise RuntimeError(reason)

        input_context = {"command": command, "cwd": cwd or os.getcwd()}

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                with self._lock:
                    self._record_success(skill_name)
                    self._save_ledger()
                return result

            # Non-zero exit = failure
            error_message = result.stderr.strip() or result.stdout.strip() or f"Exit code {result.returncode}"
            with self._lock:
                self._record_failure(
                    skill_name=skill_name,
                    error_type="SubprocessError",
                    error_message=error_message[:2000],
                    traceback_str=result.stderr[:2000] if result.stderr else "",
                    input_args=input_context,
                    exit_code=result.returncode,
                )
                self._save_ledger()
            return result

        except subprocess.TimeoutExpired as exc:
            with self._lock:
                self._record_failure(
                    skill_name=skill_name,
                    error_type="TimeoutError",
                    error_message=f"Command timed out after {timeout}s: {command}",
                    traceback_str="",
                    input_args=input_context,
                    exit_code=-1,
                )
                self._save_ledger()
            raise

    # -------------------------------------------------------------------
    # Module 3: Analyst (Surfacing)
    # -------------------------------------------------------------------

    def get_skill_health(self, skill_name: str) -> SkillHealth:
        """Get health metrics for a specific skill."""
        with self._lock:
            return self._get_health(skill_name)

    def generate_reliability_report(self) -> ReliabilityReport:
        """
        Generate a cross-skill reliability report.

        Includes:
        - Overall health summary
        - Top offenders (highest failure rates)
        - Velocity alerts (error rate spikes)
        - Pending repair ticket count
        """
        with self._lock:
            report = ReliabilityReport()
            report.total_skills_monitored = len(self._health_cache)

            for name, health in self._health_cache.items():
                # Classify skill health
                if health.is_quarantined:
                    report.quarantined_skills += 1
                elif health.failure_rate > 20:
                    report.degraded_skills += 1
                else:
                    report.healthy_skills += 1

                # Build summary
                report.skill_summaries.append({
                    "skill": name,
                    "calls": health.total_calls,
                    "failures": health.total_failures,
                    "failure_rate": health.failure_rate,
                    "deterministic_errors": health.deterministic_errors,
                    "transient_errors": health.transient_errors,
                    "circuit": health.circuit.state.value,
                    "quarantined": health.is_quarantined,
                })

            # Top offenders: sorted by deterministic error count
            report.top_offenders = sorted(
                report.skill_summaries,
                key=lambda s: s["deterministic_errors"],
                reverse=True,
            )[:5]

            # Velocity alerts — detect spikes
            # Compare last-24h errors vs previous-24h
            now = datetime.now(timezone.utc)
            day_ago = now - timedelta(days=1)
            two_days_ago = now - timedelta(days=2)

            for name, health in self._health_cache.items():
                recent = sum(
                    e.count for e in health.errors
                    if e.last_seen >= day_ago
                )
                previous = sum(
                    e.count for e in health.errors
                    if two_days_ago <= e.last_seen < day_ago
                )
                if previous > 0 and recent > previous * 2:
                    pct = int(((recent - previous) / previous) * 100)
                    report.velocity_alerts.append(
                        f"{name}: error rate increased {pct}% "
                        f"({previous} → {recent} in last 24h)"
                    )
                elif previous == 0 and recent >= 3:
                    report.velocity_alerts.append(
                        f"{name}: NEW errors detected — {recent} in last 24h "
                        f"(none previously)"
                    )

            # Count pending repair tickets
            report.repair_tickets_pending = sum(
                1 for h in self._health_cache.values()
                if h.deterministic_errors >= self.config.auto_ticket_threshold
            )

            return report

    def get_argument_correlation(self, skill_name: str) -> List[Dict[str, Any]]:
        """
        Analyze failing inputs to detect patterns.

        Looks for common keys/values across error input_args
        to identify which argument patterns trigger failures.

        Example output:
            [{"pattern": "arg 'url' contains 'localhost'", "frequency": 8}]
        """
        health = self._get_health(skill_name)
        if not health.errors:
            return []

        # Collect all failing input keys and values
        key_counts: Dict[str, int] = {}
        value_patterns: Dict[str, Dict[str, int]] = {}

        for error in health.errors:
            for k, v in error.input_args.items():
                key_counts[k] = key_counts.get(k, 0) + error.count
                v_str = str(v)[:100]
                if k not in value_patterns:
                    value_patterns[k] = {}
                value_patterns[k][v_str] = value_patterns[k].get(v_str, 0) + error.count

        correlations = []
        for key, count in sorted(key_counts.items(), key=lambda x: -x[1]):
            # Find dominant values for this key
            if key in value_patterns:
                for val, freq in sorted(value_patterns[key].items(), key=lambda x: -x[1])[:3]:
                    if freq >= 2:
                        correlations.append({
                            "pattern": f"arg '{key}' = '{val}'",
                            "frequency": freq,
                            "pct_of_errors": round(freq / health.total_failures * 100, 1) if health.total_failures else 0,
                        })

        return correlations[:10]

    # -------------------------------------------------------------------
    # Module 4: Bridge (Feed Reflection / Evolutionary Loop)
    # -------------------------------------------------------------------

    def export_for_evolution(
        self,
        min_count: int = 0,
        only_deterministic: bool = True,
        skill_filter: Optional[str] = None,
    ) -> List[RepairTicket]:
        """
        Generate RepairTickets for the Evolutionary Loop.

        Filters errors by:
        - Minimum occurrence count (default: config.auto_ticket_threshold)
        - Error class (default: deterministic only)
        - Optional skill name filter

        Returns tickets sorted by priority (critical first).
        """
        if min_count == 0:
            min_count = self.config.auto_ticket_threshold

        tickets: List[RepairTicket] = []

        with self._lock:
            for name, health in self._health_cache.items():
                if skill_filter and name != skill_filter:
                    continue

                for error in health.errors:
                    if only_deterministic and error.error_class != ErrorClass.DETERMINISTIC:
                        continue
                    if error.count < min_count:
                        continue

                    # Determine priority
                    if health.is_quarantined:
                        priority = TicketPriority.CRITICAL
                    elif health.failure_rate >= 50:
                        priority = TicketPriority.HIGH
                    elif error.count >= 10:
                        priority = TicketPriority.HIGH
                    elif error.count >= 5:
                        priority = TicketPriority.MEDIUM
                    else:
                        priority = TicketPriority.LOW

                    # Try to locate skill source
                    skill_path, skill_source = self._locate_skill_source(name)

                    # Suggest fix approach based on error type
                    fix_approach = self._suggest_fix(error)

                    ticket = RepairTicket(
                        ticket_id=f"{error.fingerprint}-{int(error.last_seen.timestamp())}",
                        priority=priority,
                        skill_name=name,
                        skill_path=skill_path,
                        skill_source=skill_source,
                        error_summary=(
                            f"{name}: {error.error_type} — {error.error_message[:100]} "
                            f"({error.count}x, {error.error_class.value})"
                        ),
                        error_class=error.error_class,
                        error_type=error.error_type,
                        error_message=error.error_message,
                        traceback=error.traceback,
                        failing_input=error.input_args,
                        occurrence_count=error.count,
                        first_seen=error.first_seen,
                        last_seen=error.last_seen,
                        failure_rate=health.failure_rate,
                        suggested_fix_approach=fix_approach,
                    )
                    tickets.append(ticket)

        # Sort: critical → high → medium → low
        priority_order = {
            TicketPriority.CRITICAL: 0,
            TicketPriority.HIGH: 1,
            TicketPriority.MEDIUM: 2,
            TicketPriority.LOW: 3,
        }
        tickets.sort(key=lambda t: (priority_order[t.priority], -t.occurrence_count))
        return tickets

    def export_evolution_payload(self, **kwargs) -> str:
        """
        Export tickets as a single LLM-readable string.

        This is the primary output method — produces a document
        that can be fed directly into skill-evolutionary-loop Phase 3
        as context for the reflection agent.
        """
        tickets = self.export_for_evolution(**kwargs)
        if not tickets:
            return "# No repair tickets pending.\nAll monitored skills are operating within acceptable parameters."

        sections = [
            "# Skill Runtime Monitor — Repair Tickets for Evolutionary Loop",
            f"*Generated: {datetime.now(timezone.utc).isoformat()}*",
            f"*Tickets: {len(tickets)}*",
            "",
        ]
        for ticket in tickets:
            sections.append(ticket.to_llm_prompt())
            sections.append("---\n")

        return "\n".join(sections)

    def _locate_skill_source(self, skill_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Try to find and read the source code of a skill."""
        # Search common skill locations
        search_paths = [
            self.workspace / "skills" / skill_name / "SKILL.md",
            self.workspace / "skills" / skill_name / "scripts",
        ]
        for path in search_paths:
            if path.exists():
                if path.is_file():
                    try:
                        return str(path), path.read_text()[:5000]
                    except Exception:
                        return str(path), None
                elif path.is_dir():
                    # Read first .py file in scripts dir
                    for py in sorted(path.glob("*.py")):
                        try:
                            return str(py), py.read_text()[:5000]
                        except Exception:
                            return str(py), None
        return None, None

    def _suggest_fix(self, error: ErrorLog) -> str:
        """Suggest a fix approach based on error patterns."""
        et = error.error_type.lower()
        em = error.error_message.lower()

        if "keyerror" in et:
            return "Add defensive key access (dict.get() or 'in' check) for the missing key."
        if "typeerror" in et and "nonetype" in em:
            return "Add null/None guard before accessing the attribute or calling the method."
        if "indexerror" in et:
            return "Add bounds checking before list/array access."
        if "importerror" in et or "modulenotfounderror" in et:
            return "Check dependency installation. Add to requirements or handle import gracefully."
        if "filenotfounderror" in et:
            return "Verify file path exists before access. Use pathlib with .exists() check."
        if "permission" in em:
            return "Check file/directory permissions. May need chmod or run as different user."
        if "validationerror" in et or "pydantic" in em:
            return "Input doesn't match expected schema. Add input validation/coercion before processing."
        if "assertionerror" in et:
            return "An assertion failed — review the assumption being asserted and fix the logic."
        return "Analyze the traceback and failing input to identify root cause."

    # -------------------------------------------------------------------
    # Maintenance
    # -------------------------------------------------------------------

    def prune_all(self) -> Dict[str, int]:
        """Prune old errors from all skills. Returns count of removed entries."""
        removed = {}
        with self._lock:
            for name, health in self._health_cache.items():
                before = len(health.errors)
                self._prune_errors(health)
                after = len(health.errors)
                if before > after:
                    removed[name] = before - after
            self._save_ledger()
        return removed

    def reset_circuit(self, skill_name: str) -> bool:
        """Manually reset a skill's circuit breaker to CLOSED."""
        with self._lock:
            health = self._get_health(skill_name)
            health.circuit = CircuitState()
            self._save_ledger()
            return True

    def clear_skill(self, skill_name: str) -> bool:
        """Clear all monitoring data for a skill."""
        with self._lock:
            if skill_name in self._health_cache:
                del self._health_cache[skill_name]
                self._save_ledger()
                return True
            return False


# ---------------------------------------------------------------------------
# Decorator API
# ---------------------------------------------------------------------------

def monitor_skill(monitor: SkillMonitor, skill_name: Optional[str] = None):
    """
    Decorator to wrap a skill function with monitoring.

    Usage:
        monitor = SkillMonitor()

        @monitor_skill(monitor)
        def my_tool(arg1, arg2):
            """Handle this operation."""
            ...

        @monitor_skill(monitor, skill_name="custom-name")
        def another_tool():
            """Handle this operation."""
            ...
    """
    def decorator(fn: Callable) -> Callable:
        """Handle this operation."""
        name = skill_name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            """Handle this operation."""
            return monitor.execute(name, fn, args, kwargs)

        # Attach metadata for introspection
        wrapper._monitored = True
        wrapper._skill_name = name
        wrapper._monitor = monitor
        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_repr(value: Any, max_len: int = 500) -> Any:
    """Safely represent a value for logging. Truncate large objects."""
    try:
        if isinstance(value, (str, int, float, bool, type(None))):
            if isinstance(value, str) and len(value) > max_len:
                return value[:max_len] + "..."
            return value
        if isinstance(value, (list, tuple)):
            return f"[{type(value).__name__}, len={len(value)}]"
        if isinstance(value, dict):
            return f"{{dict, keys={list(value.keys())[:10]}}}"
        return str(value)[:max_len]
    except Exception:
        return "<unrepresentable>"


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    """CLI for inspecting monitor state."""
    if len(sys.argv) < 2:
        print("Usage: monitor.py <command> [args]")
        print("Commands: status, tickets, health <skill>, prune, export [--output FILE], reset <skill>")
        sys.exit(1)

    command = sys.argv[1]

    # Determine workspace
    workspace = os.environ.get("OPENCLAW_WORKSPACE", os.getcwd())
    monitor = SkillMonitor(workspace=workspace)

    if command == "status":
        report = monitor.generate_reliability_report()
        print(report.to_summary())

    elif command == "tickets":
        payload = monitor.export_evolution_payload()
        print(payload)

    elif command == "health":
        if len(sys.argv) < 3:
            print("Usage: monitor.py health <skill_name>")
            sys.exit(1)
        name = sys.argv[2]
        health = monitor.get_skill_health(name)
        print(json.dumps(health.model_dump(mode="json"), indent=2, default=str))

        # Include argument correlation
        corr = monitor.get_argument_correlation(name)
        if corr:
            print("\n## Argument Correlations")
            for c in corr:
                print(f"  {c['pattern']} — {c['frequency']}x ({c['pct_of_errors']}% of errors)")

    elif command == "prune":
        removed = monitor.prune_all()
        if removed:
            for skill, count in removed.items():
                print(f"Pruned {count} old entries from {skill}")
        else:
            print("Nothing to prune.")

    elif command == "export":
        payload = monitor.export_evolution_payload()
        if len(sys.argv) > 2 and sys.argv[2] == "--output":
            output_path = Path(sys.argv[3])
            output_path.write_text(payload)
            print(f"Exported to {output_path}")
        else:
            print(payload)

    elif command == "reset":
        if len(sys.argv) < 3:
            print("Usage: monitor.py reset <skill_name>")
            sys.exit(1)
        monitor.reset_circuit(sys.argv[2])
        print(f"Circuit breaker for '{sys.argv[2]}' reset to CLOSED.")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
