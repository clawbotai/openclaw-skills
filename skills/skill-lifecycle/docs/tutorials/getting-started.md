# Getting Started with skill-lifecycle

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **skill-lifecycle** skill — combining the evolutionary loop and runtime monitor.

---

## What You'll Learn

- How the evolutionary loop and runtime monitor work together
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/skill-lifecycle/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/skill-lifecycle/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Evolutionary Loop (loop_manager.py)

```bash
python3 skills/skill-lifecycle/scripts/loop_manager.py --help
```

## Step 4: Runtime Monitor (monitor.py)

```bash
python3 skills/skill-lifecycle/scripts/monitor.py --help
```

## Step 5: Monitor Schemas

```bash
python3 skills/skill-lifecycle/scripts/schemas.py --help
```

## Step 6: Usage Example

```bash
python3 skills/skill-lifecycle/scripts/usage_example.py --help
```

## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
