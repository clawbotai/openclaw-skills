# Getting Started with quarter-hour-updates

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **quarter-hour-updates** skill effectively.

---

## What You'll Learn

- How quarter-hour-updates integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/quarter-hour-updates/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/quarter-hour-updates/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run cerebro_tick.py

```bash
python3 skills/quarter-hour-updates/scripts/cerebro_tick.py --help\n```\n\nExplore available commands and options.\n
## Step 4: Run daemon.py

```bash
python3 skills/quarter-hour-updates/scripts/daemon.py --help\n```\n\nExplore available commands and options.\n
## Step 5: Run log_progress.py

```bash
python3 skills/quarter-hour-updates/scripts/log_progress.py --help\n```\n\nExplore available commands and options.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
