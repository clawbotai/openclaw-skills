# Contributing to email-manager

Guidelines for contributing to the **email-manager** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/email-manager
cat SKILL.md
```

## Structure

```
email-manager/
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

## Workflow

1. Read SKILL.md before making changes
2. Never remove existing SKILL.md content
3. Test all script changes locally
4. Update CHANGELOG.md with your changes
5. Verify docs: `bash skills/docs-engine/scripts/score-docs.sh skills/email-manager`

## Commits

```
feat(email-manager): description
fix(email-manager): description
docs(email-manager): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
