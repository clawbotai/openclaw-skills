# Contributing to quarter-hour-updates

Guidelines for contributing to the **quarter-hour-updates** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/quarter-hour-updates
cat SKILL.md
```

## Structure

```
quarter-hour-updates/
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
5. Verify docs: `bash skills/master-docs/scripts/score-docs.sh skills/quarter-hour-updates`

## Commits

```
feat(quarter-hour-updates): description
fix(quarter-hour-updates): description
docs(quarter-hour-updates): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
