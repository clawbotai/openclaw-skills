# Contributing to sw-mobile-architect

Guidelines for contributing to the **sw-mobile-architect** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/mobile-architect
cat SKILL.md
```

## Structure

```
sw-mobile-architect/
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
5. Verify docs: `bash skills/docs-engine/scripts/score-docs.sh skills/mobile-architect`

## Commits

```
feat(sw-mobile-architect): description
fix(sw-mobile-architect): description
docs(sw-mobile-architect): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
