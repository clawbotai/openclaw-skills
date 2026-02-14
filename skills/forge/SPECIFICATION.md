# SPECIFICATION.md
Generated: 2026-02-13 | Confidence: High

## Objective
Bring the forge skill from documentation-only to a fully operational skill with CLI scripts, monitor integration, and clear invocation patterns.

## Requirements

### Functional
- **Mode 1 (Code Gen):** `python3 scripts/forge.py mode1 "build X"` — delegates a freeform prompt to Gemini via the Antigravity Forge Daemon, returns an IntegrationManifest.
- **Mode 2 (Skill × Skill):** `python3 scripts/forge.py mode2 <operator> <target>` — reads operator SKILL.md + target skill files + today's memory, packs into a forge job, returns manifest.
- Both modes communicate with the daemon via stdio JSON-RPC (spawn subprocess).
- Output: JSON IntegrationManifest to stdout (architecturalSummary, operations[], requiredCommands[]).
- Health check: verify daemon binary exists before spawning.
- Polling: 5s interval, report state to stderr, timeout after 5 minutes.

### Non-Functional
- Python 3.9 compatible (typing.Optional[X], not X | None)
- stdlib-only (no pip dependencies)
- Scripts under 300 lines each
- No sys.exit() in library functions

## Technical Decisions

### Decision: stdio over HTTP transport
- Rationale: stdio is simpler (no session negotiation), stateless per invocation, no port conflicts
- Trade-off: can't share jobs across invocations (acceptable — each forge call is independent)

### Decision: Lightweight monitor (not full skill-lifecycle monitor)
- Rationale: forge is a meta-skill, not a high-frequency automation. Full circuit breaker overkill.
- Implementation: log failures to JSON, classify errors, simple threshold check before invocation.

## Acceptance Criteria
- [ ] `python3 scripts/forge.py mode1 "hello world"` submits, polls, returns manifest JSON
- [ ] `python3 scripts/forge.py mode2 lifecycle forge` reads both skills, submits, returns manifest
- [ ] Failures logged to memory/forge-errors.json with classification
- [ ] SKILL.md documents both CLI modes with examples
