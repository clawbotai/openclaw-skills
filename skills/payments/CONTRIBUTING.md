# Contributing to master-payments

Guidelines for contributing to the **master-payments** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/payments
cat SKILL.md
```

## Structure

```
master-payments/
├── SKILL.md           # Skill definition (source of truth)
├── README.md          # Overview and usage
├── CONTRIBUTING.md    # This file
├── CHANGELOG.md       # Version history
├── scripts/           # Automation scripts
└── docs/              # Diátaxis documentation
```

## Language Guidelines

### Documentation

- Follow Diátaxis framework
- Include code examples in Markdown

## Workflow

1. Read SKILL.md before making changes
2. Never remove existing SKILL.md content
3. Test all script changes locally
4. Update CHANGELOG.md with your changes
5. Verify docs: `bash skills/docs-engine/scripts/score-docs.sh skills/payments`

## Commits

```
feat(master-payments): description
fix(master-payments): description
docs(master-payments): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
