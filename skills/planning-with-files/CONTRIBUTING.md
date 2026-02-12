# Contributing to planning-with-files

Guidelines for contributing to the **planning-with-files** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/planning-with-files
cat SKILL.md
```

## Structure

```
planning-with-files/
├── SKILL.md           # Skill definition (source of truth)
├── README.md          # Overview and usage
├── CONTRIBUTING.md    # This file
├── CHANGELOG.md       # Version history
├── scripts/           # Automation scripts
└── docs/              # Diátaxis documentation
```

## Language Guidelines

### Python

- Python 3.11+
- PEP 8 style, type hints
- Docstrings on all public functions

### Bash

- Use `set -euo pipefail`
- Add `--help` support
- Header comments with purpose
- Lint: `shellcheck scripts/*.sh`

## Workflow

1. Read SKILL.md before making changes
2. Never remove existing SKILL.md content
3. Test all script changes locally
4. Update CHANGELOG.md with your changes
5. Verify docs: `bash skills/master-docs/scripts/score-docs.sh skills/planning-with-files`

## Commits

```
feat(planning-with-files): description
fix(planning-with-files): description
docs(planning-with-files): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
