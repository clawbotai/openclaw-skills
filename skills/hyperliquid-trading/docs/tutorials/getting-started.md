# Getting Started with hyperliquid-trading

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **hyperliquid-trading** skill effectively.

---

## What You'll Learn

- How hyperliquid-trading integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/hyperliquid-trading/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/hyperliquid-trading/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run analyze-coingecko.mjs

```bash
node skills/hyperliquid-trading/scripts/analyze-coingecko.mjs\n```\n
## Step 4: Run analyze-market.mjs

```bash
node skills/hyperliquid-trading/scripts/analyze-market.mjs\n```\n
## Step 5: Run check-positions.mjs

```bash
node skills/hyperliquid-trading/scripts/check-positions.mjs\n```\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
