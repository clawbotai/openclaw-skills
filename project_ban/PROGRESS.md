# PROGRESS.md — Project B.A.N.

## Iteration 1 — 2026-02-14T13:48Z
Task: Initial codebase generation (all 13 files)
Result: PASS (compile)
Gates:
- Compile: PASS (all 11 source files)
- Lint: FAIL (1 error — f-string without placeholders in orchestrator.py:114)
- Typecheck: FAIL (missing stubs for paramiko, yaml)
- Validation: FAIL (YAML `permitted_garments: None` when all items commented out)
Next: Fix lint, install stubs, handle None coercion

## Iteration 2 — 2026-02-14T13:55Z
Task: Fix all gate failures from iteration 1
Result: PASS (all gates)
Fixes applied:
1. **Lint** — Removed extraneous `f` prefix from string literal in orchestrator.py:114
2. **Typecheck** — Installed `types-paramiko` and `types-PyYAML` stubs
3. **Validation** — Added `@model_validator(mode="before")` to coerce `None` → `[]` for `permitted_garments` (YAML parses commented-out list as None)
4. **Post-strip behavior** — Changed b4_sanitizer post-strip verification from RuntimeError to warning log (daemons may respawn; spec says warn, not abort)
Gates:
- Compile: PASS
- Lint: PASS (ruff — 0 errors)
- Typecheck: PASS (mypy — 0 errors, 11 files)
- Validation: PASS (sample YAML loads, merged allowlist = 7 core daemons)

## Status: COMPLETE ✅

### Files
```
project_ban/
├── pyproject.toml              # Project metadata + deps + entry point
├── ban_payload.yaml            # Sample config (validated)
├── PROGRESS.md                 # This file
├── src/
│   ├── __init__.py
│   ├── cli.py                  # Typer CLI (strip + validate commands)
│   ├── orchestrator.py         # FSM loop (DRESSED → NIRVANA)
│   ├── ssh_manager.py          # Paramiko wrapper (context manager)
│   ├── schemas.py              # Pydantic v2 strict model + allowlist merge
│   ├── audit.py                # JSON audit log
│   └── boundaries/
│       ├── __init__.py
│       ├── b2_profiler.py      # Pre-flight anatomy check
│       ├── b3_anchor.py        # APFS snapshot + Dead Man's Switch
│       ├── b4_sanitizer.py     # Daemon strip-down (bootout + disable)
│       └── b5_qos.py           # nice + caffeinate workload launch
```

### Quality Gates (final)
- ruff: 0 errors
- mypy: 0 errors (11 files, strict)
- compileall: all modules compile
- Config validation: sample YAML → BanPayload → 7-daemon merged allowlist ✓

### Bugs Found & Fixed
1. f-string without placeholders (cosmetic)
2. Missing type stubs (dev dependency)
3. YAML None coercion for empty list (real bug — would crash on any config with commented-out permitted_garments)
4. Post-strip verification too aggressive (would abort on respawning daemons)

## Iteration 3 — 2026-02-14T14:10Z (Live deployment #1)
Task: Run B.A.N. against 192.168.10.139 (clawbotai)
Result: NIRVANA achieved, but Wi-Fi killed → machine unreachable
Fixes:
- `launchctl disable` is PERSISTENT across reboots (spec was wrong)
- DMS must `launchctl enable` all daemons before reboot, not rely on snapshot
- Added `WIFI_SURVIVAL_DAEMONS` (7 daemons) + `use_wifi` config flag
- Added `ban restore` CLI command + `restore_all_disabled()` function
- Password auth: SSHManager now uses Paramiko stdin.write() for sudo -S

## Iteration 4 — 2026-02-14T14:28Z (DMS fix)
Task: Fix DMS process dying immediately after arming
Result: PASS
Fixes:
- `echo pw | sudo -S nohup &` breaks backgrounding (pipe conflict)
- Solution: base64-encode DMS script → write to /tmp → launch via `sudo bash -c 'nohup /script </dev/null >log 2>&1 & echo $!'`
- `</dev/null` fully detaches stdin so process survives SSH channel close
- DMS PID now written to /tmp/ban_dms.pid by the script itself (reliable PID tracking)

## Iteration 5 — 2026-02-14T14:33Z (tmutil + strip)
Task: Fix tmutil exit 73, run full strip
Result: NIRVANA achieved (106 daemons stripped)
Fixes:
- Added `skip_snapshot` config flag for when tmutil fails
- tmutil exits 73 with existing snapshots — cause unclear (not disk space)

## Iteration 6 — 2026-02-14T14:43Z (Batching + restore)
Task: Fix performance (212 SSH round-trips) and restore timeout
Fixes:
- Batched all bootout+disable into single SSH command (was 2×N round-trips)
- Batched all enable into single SSH command for restore
- `restore_all_disabled()` now writes a script to target and executes it (avoids command length limits)
- Added SSH connection retry with backoff (3 attempts, 5s/10s delay)
- Added configurable timeout per SSH command
- DMS disarm failure diagnosed: PID from `echo $!` was shell PID, not script PID

## Known Issues (remaining)
- SSH rate limiting: macOS sshd throttles rapid connections → need longer pauses between test runs
- tmutil snapshot creation fails (exit 73) — cause unknown, skip_snapshot workaround in place
- Multiple B.A.N. runs stack disabled overrides — restore must be run between runs
