# Getting Started with web-deploy-github

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **web-deploy-github** skill effectively.

---

## What You'll Learn

- How web-deploy-github integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/web-deploy-github/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/web-deploy-github/SKILL.md
```

Understand the triggers, workflow steps, and safety considerations.

## Step 3: Run deploy_github_pages.sh

```bash
bash skills/web-deploy-github/scripts/deploy_github_pages.sh --help\n```\n\nReview output to understand capabilities.\n
## Step 4: Run init_project.sh

```bash
bash skills/web-deploy-github/scripts/init_project.sh --help\n```\n\nReview output to understand capabilities.\n
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
