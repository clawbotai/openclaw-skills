# Getting Started with filesystem-standard

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **filesystem-standard** skill effectively.

---

## What You'll Learn

- How filesystem-standard integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/filesystem-standard/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/filesystem-standard/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run audit-filesystem.sh

```bash
bash skills/filesystem-standard/scripts/audit-filesystem.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 4: Run cleanup-stale.sh

```bash
bash skills/filesystem-standard/scripts/cleanup-stale.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 5: Run enforce-permissions.sh

```bash
bash skills/filesystem-standard/scripts/enforce-permissions.sh --help\n```\n\nReview output to understand capabilities.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
