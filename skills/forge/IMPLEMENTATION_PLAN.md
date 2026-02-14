# IMPLEMENTATION_PLAN.md

## Tasks (priority order)
- [ ] **Upgrade Monitor**: Replace `monitor_wrapper.py` with `scripts/monitor.py` implementing the full `skill-lifecycle` spec (error classification, repair ticket generation, circuit breaker).
- [ ] **Update CLI**: Refactor `scripts/forge.py` to use the new `scripts/monitor.py` and handle specific failure modes of the v3.0 daemon (e.g., auth missing).
- [ ] **Add Tests**: Create `tests/test_forge.py` and `tests/test_monitor.py` to verify CLI logic and circuit breaker behavior.
- [ ] **Configure Gates**: Establish `lint` (ruff/pylint) and `typecheck` (mypy) gates for the python scripts.
- [ ] **Verify Daemon**: Run a live test of Mode 1 against the v3.0 daemon to ensure JSON-RPC compatibility.

## Backlog
- [ ] Add `mode3` for purely architectural review (no code generation).
- [ ] Implement distinct error handling for `gemini-3-pro-preview` rate limits.
