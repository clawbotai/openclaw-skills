# Contributing to business-development

Guidelines for contributing to the **business-development** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/business-development
cat SKILL.md
```

## Structure

```
business-development/
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
5. Verify docs: `bash skills/master-docs/scripts/score-docs.sh skills/business-development`

## Commits

```
feat(business-development): description
fix(business-development): description
docs(business-development): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
