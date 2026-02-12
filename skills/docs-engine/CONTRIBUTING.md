# Contributing to master-docs

Guidelines for contributing to the **master-docs** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/docs-engine
cat SKILL.md
```

## Structure

```
master-docs/
├── SKILL.md           # Skill definition (source of truth)
├── README.md          # Overview and usage
├── CONTRIBUTING.md    # This file
├── CHANGELOG.md       # Version history
├── scripts/           # Automation scripts
└── docs/              # Diátaxis documentation
```

## Language Guidelines

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
5. Verify docs: `bash skills/docs-engine/scripts/score-docs.sh skills/docs-engine`

## Commits

```
feat(master-docs): description
fix(master-docs): description
docs(master-docs): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
