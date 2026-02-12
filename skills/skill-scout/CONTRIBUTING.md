# Contributing to skill-scout

## Setup

No pip installs needed. Just Python 3.9+ and optionally `clawhub` + `gh` CLIs.

```bash
cd skills/skill-scout
python3 -m unittest discover -s tests -v  # Run all tests
```

## Code Standards

- **Python 3.9 strict**: Use `typing.Optional[X]`, `typing.List[X]`, `typing.Dict[K,V]`. Never `X | None` or `list[X]`.
- **Zero dependencies**: stdlib only. No pip installs.
- **Google-style docstrings**: Every function gets Args/Returns sections.
- **Module docstrings**: Every .py file starts with a triple-quoted description.
- **JSON on stdout**: All CLI output is `json.dumps()` via `common.json_out()`. Logs go to stderr.

## Architecture

| File | Role |
|------|------|
| `scripts/common.py` | Shared DB, shell wrapper, logging, utilities |
| `scripts/discover.py` | Discovery: ClawHub, GitHub, awesome lists |
| `scripts/evaluate.py` | Scoring: 7 dimensions, AST security, regex credentials |
| `scripts/scout.py` | Orchestrator: ranking, gaps, acquisition, watch, reports |
| `tests/test_*.py` | Unit tests (stdlib unittest) |

## Adding a New Scoring Dimension

1. In `evaluate.py`, create `_score_<name>(files) -> DimensionScore`
2. Add it to the `evaluate_skill()` function's `dims` list
3. Update `SKILL.md` scoring table
4. Add tests in `tests/test_evaluate.py`

## Adding a New Discovery Source

1. In `discover.py`, add a search function following the pattern of `search_clawhub()`
2. Include circuit breaker support (`_record_failure`/`_record_success`)
3. Register a new CLI subcommand in `main()`
4. Store results in the `skills` table with appropriate `source` value
5. Add parsing tests in `tests/test_discover.py`

## Testing

All tests use `unittest` from stdlib. No pytest needed.

```bash
# Run all tests
python3 -m unittest discover -s tests -v

# Run a specific test file
python3 -m unittest tests.test_evaluate -v

# Run a specific test
python3 -m unittest tests.test_evaluate.TestSecurityAST.test_detects_eval_with_dynamic_arg
```

## PR Process

1. Make changes on a branch
2. Run tests: `python3 -m unittest discover -s tests -v`
3. Check CLIs work: `python3 scripts/discover.py --help` etc.
4. Verify Python 3.9 syntax: no `X | None`, no `list[X]`
5. Commit with descriptive message
