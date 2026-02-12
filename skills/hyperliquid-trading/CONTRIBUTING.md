# Contributing to hyperliquid-trading

Guidelines for contributing to the **hyperliquid-trading** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/hyperliquid-trading
cat SKILL.md
```

## Structure

```
hyperliquid-trading/
├── SKILL.md           # Skill definition (source of truth)
├── README.md          # Overview and usage
├── CONTRIBUTING.md    # This file
├── CHANGELOG.md       # Version history
├── scripts/           # Automation scripts
└── docs/              # Diátaxis documentation
```

## Language Guidelines

### JavaScript

- ES modules
- JSDoc on exports
- Node.js 18+

## Workflow

1. Read SKILL.md before making changes
2. Never remove existing SKILL.md content
3. Test all script changes locally
4. Update CHANGELOG.md with your changes
5. Verify docs: `bash skills/master-docs/scripts/score-docs.sh skills/hyperliquid-trading`

## Commits

```
feat(hyperliquid-trading): description
fix(hyperliquid-trading): description
docs(hyperliquid-trading): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
