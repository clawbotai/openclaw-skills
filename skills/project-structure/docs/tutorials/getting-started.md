# Getting Started with project-structure

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **project-structure** skill effectively.

---

## What You'll Learn

- How project-structure integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/project-structure/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/project-structure/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run scaffold.sh

```bash
bash skills/project-structure/scripts/scaffold.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 4: Run validate-structure.sh

```bash
bash skills/project-structure/scripts/validate-structure.sh --help\n```\n\nReview output to understand capabilities.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
