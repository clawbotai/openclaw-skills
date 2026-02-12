# Contributing to web-deploy-github

Guidelines for contributing to the **web-deploy-github** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/web-deploy-github
cat SKILL.md
```

## Structure

```
web-deploy-github/
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
5. Verify docs: `bash skills/docs-engine/scripts/score-docs.sh skills/web-deploy-github`

## Commits

```
feat(web-deploy-github): description
fix(web-deploy-github): description
docs(web-deploy-github): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
