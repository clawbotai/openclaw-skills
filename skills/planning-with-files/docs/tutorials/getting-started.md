# Getting Started with planning-with-files

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **planning-with-files** skill effectively.

---

## What You'll Learn

- How planning-with-files integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/planning-with-files/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/planning-with-files/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run check-complete.sh

```bash
bash skills/planning-with-files/scripts/check-complete.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 4: Run init-session.sh

```bash
bash skills/planning-with-files/scripts/init-session.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 5: Run session-catchup.py

```bash
python3 skills/planning-with-files/scripts/session-catchup.py --help\n```\n\nExplore available commands and options.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
