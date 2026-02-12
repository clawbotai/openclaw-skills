# Contributing to sveltekit-webapp

Guidelines for contributing to the **sveltekit-webapp** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/sveltekit-webapp
cat SKILL.md
```

## Structure

```
sveltekit-webapp/
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
5. Verify docs: `bash skills/master-docs/scripts/score-docs.sh skills/sveltekit-webapp`

## Commits

```
feat(sveltekit-webapp): description
fix(sveltekit-webapp): description
docs(sveltekit-webapp): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
