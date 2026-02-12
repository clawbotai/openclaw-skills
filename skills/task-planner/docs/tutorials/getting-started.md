# Getting Started with natural-language-planner

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **natural-language-planner** skill effectively.

---

## What You'll Learn

- How natural-language-planner integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/task-planner/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/task-planner/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run __init__.py

```bash
python3 skills/task-planner/scripts/__init__.py --help\n```\n\nExplore available commands and options.\n
## Step 4: Run __main__.py

```bash
python3 skills/task-planner/scripts/__main__.py --help\n```\n\nExplore available commands and options.\n
## Step 5: Run config_manager.py

```bash
python3 skills/task-planner/scripts/config_manager.py --help\n```\n\nExplore available commands and options.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
