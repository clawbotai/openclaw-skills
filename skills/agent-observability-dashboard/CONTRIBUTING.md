# Contributing to agent-observability-dashboard

Guidelines for contributing to the **agent-observability-dashboard** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/agent-observability-dashboard
cat SKILL.md
```

## Structure

```
agent-observability-dashboard/
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
5. Verify docs: `bash skills/master-docs/scripts/score-docs.sh skills/agent-observability-dashboard`

## Commits

```
feat(agent-observability-dashboard): description
fix(agent-observability-dashboard): description
docs(agent-observability-dashboard): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
