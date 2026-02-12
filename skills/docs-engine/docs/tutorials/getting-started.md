# Getting Started with master-docs

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **master-docs** skill effectively.

---

## What You'll Learn

- How master-docs integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/docs-engine/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/docs-engine/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run document.sh

```bash
bash skills/docs-engine/scripts/document.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 4: Run inject-help.sh

```bash
bash skills/docs-engine/scripts/inject-help.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 5: Run score-docs.sh

```bash
bash skills/docs-engine/scripts/score-docs.sh --help\n```\n\nReview output to understand capabilities.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
