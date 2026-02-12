# SPECIFICATION.md — Skill Scout Evolution
*Generated: 2026-02-12 | Sources: Full code review (3,300 LOC) | Confidence: High*

## Objective

Harden skill-scout's reliability, close real security gaps, add test coverage for new security features, and fix operational bugs. No feature additions — this is a quality+security pass.

## Current State Analysis

### What's Solid
- Well-structured 4-file architecture (common/discover/evaluate/scout)
- Thread-safe SQLite with WAL mode + write lock
- Circuit breaker on CLI tools (clawhub/gh)
- Hardcoded Python 3.9 stdlib set (no sys.stdlib_module_names trap)
- 29 passing unit tests
- Security tier-cap prevents high-starred malicious skills from S/A/B
- AST analysis for eval/exec/os.system/shell=True/pickle
- Markdown security scanner (just added)
- AST evasion detection for __import__/importlib/getattr (just added)

### Problems Found

1. **discover.py: db_write inside ThreadPoolExecutor** — `sweep_categories` runs `_search_category` in 5 threads, and each calls `search_clawhub`/`search_github` which call `db_write` individually. While `_write_lock` serializes writes, each thread calls `db_write` per-skill in a loop (N writes per thread). Should batch with `db_write_many` for performance.

2. **discover.py: no error boundary in thread workers** — If `_search_category` raises an unexpected exception, `as_completed` catches it, but the thread's DB connection may be left in a bad state. Need explicit exception handling inside the worker.

3. **evaluate.py: `collect_remote_files` has circular import** — It does `from discover import fetch_github_file` at call time (lazy import). This works but is fragile. Same pattern in `scout.py` with `from evaluate import evaluate_skill`.

4. **scout.py: `acquire_skill` doesn't quarantine** — Skills go straight from evaluation to `skills/` directory. Should land in a `_quarantine/` directory first, get evaluated there, then move on approval.

5. **No tests for markdown scanner or AST evasion** — The security features I just added have zero test coverage.

6. **discover.py: `parse_awesome_list` writes per-skill in a loop** — Hundreds of individual `db_write` calls. Should batch.

7. **common.py: `run_shell` doesn't sanitize arguments** — Not exploitable since all callers use list args (not shell=True), but should document this invariant.

8. **SKILL.md: security rules section outdated** — Doesn't mention markdown scanning or AST evasion detection.

## Tasks (Priority Order)

- [ ] T1: Add quarantine directory workflow to `acquire_skill` (security)
- [ ] T2: Add tests for markdown scanner + AST evasion detection (quality)
- [ ] T3: Batch DB writes in `discover.py` (performance)
- [ ] T4: Add error boundary in thread workers (reliability)
- [ ] T5: Update SKILL.md security rules section (documentation)

## Acceptance Criteria

- [ ] All 29 existing tests still pass
- [ ] New tests for markdown scanner (curl|sh, suspicious URLs, obfuscation)
- [ ] New tests for AST evasion (__import__, importlib, getattr)
- [ ] `acquire_skill` downloads to `_quarantine/`, evaluates there, moves on pass
- [ ] `sweep_categories` uses `db_write_many` for batch inserts
- [ ] SKILL.md documents markdown scanning + evasion detection
- [ ] Zero external dependencies, Python 3.9 compatible
