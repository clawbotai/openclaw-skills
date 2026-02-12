# Getting Started with product-manager-toolkit

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **product-manager-toolkit** skill effectively.

---

## What You'll Learn

- How product-manager-toolkit integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/product-management/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/product-management/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run customer_interview_analyzer.py

```bash
python3 skills/product-management/scripts/customer_interview_analyzer.py --help\n```\n\nExplore available commands and options.\n
## Step 4: Run rice_prioritizer.py

```bash
python3 skills/product-management/scripts/rice_prioritizer.py --help\n```\n\nExplore available commands and options.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
