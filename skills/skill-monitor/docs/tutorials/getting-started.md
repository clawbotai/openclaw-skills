# Getting Started with skill-runtime-monitor

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **skill-runtime-monitor** skill effectively.

---

## What You'll Learn

- How skill-runtime-monitor integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/skill-monitor/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/skill-monitor/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run monitor.py

```bash
python3 skills/skill-monitor/scripts/monitor.py --help\n```\n\nExplore available commands and options.\n
## Step 4: Run schemas.py

```bash
python3 skills/skill-monitor/scripts/schemas.py --help\n```\n\nExplore available commands and options.\n
## Step 5: Run usage_example.py

```bash
python3 skills/skill-monitor/scripts/usage_example.py --help\n```\n\nExplore available commands and options.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
