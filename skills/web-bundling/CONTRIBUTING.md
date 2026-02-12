# Contributing to web-bundling

Guidelines for contributing to the **web-bundling** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/web-bundling
cat SKILL.md
```

## Structure

```
web-bundling/
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
5. Verify docs: `bash skills/master-docs/scripts/score-docs.sh skills/web-bundling`

## Commits

```
feat(web-bundling): description
fix(web-bundling): description
docs(web-bundling): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
