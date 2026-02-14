---
name: openclaw-kb
description: OpenClaw knowledge base — comprehensive reference for Gateway configuration, channels, tools, sessions, security, plugins, skills, models, multi-agent routing, sandboxing, slash commands, and troubleshooting. Use when answering any question about OpenClaw architecture, config, or operations.
metadata: {"openclaw": {"always": true}}
---

# OpenClaw Knowledge Base

You have access to a comprehensive OpenClaw documentation knowledge base at `{baseDir}/docs/`.

## When to use
- Any question about OpenClaw configuration, architecture, or operations
- Debugging OpenClaw issues (config validation, gateway errors, channel problems)
- Setting up channels (WhatsApp, Telegram, Discord, Slack, Signal, iMessage, Google Chat, etc.)
- Model selection, failover, aliases, and provider configuration
- Multi-agent routing, bindings, and per-agent sandbox/tool policies
- Session management, compaction, pruning, and reset policies
- Security hardening, DM policies, sandboxing, and elevated exec
- Skills, plugins, and ClawHub
- Slash commands and directives
- Updating, migrating, and troubleshooting

## How to use
1. Read the relevant doc file from `{baseDir}/docs/` based on the topic
2. Key files:
   - `gateway-runbook.md` — startup, runtime model, supervision, operations
   - `configuration-reference.md` — FULL config schema (channels, agents, tools, sessions, etc.)
   - `security.md` — security audit, DM policies, sandboxing, prompt injection, hardening
   - `sandboxing.md` — Docker sandbox modes, scopes, workspace access
   - `multi-agent.md` — routing, bindings, per-agent overrides
   - `multi-agent-sandbox-tools.md` — tool filtering precedence, per-agent sandbox
   - `models.md` — model selection, /model CLI, scanning, registry
   - `sessions.md` — session keys, DM scope, lifecycle, reset, send policy
   - `slash-commands.md` — all / commands and directives
   - `skills.md` — skill format, gating, config, ClawHub, token impact
   - `plugins.md` — plugin API, discovery, channels, providers, hooks
   - `compaction.md` — context window management
   - `updating.md` — update paths, rollback, doctor
   - `faq.md` — common questions and troubleshooting
   - `getting-started.md` — initial setup
   - `environment.md` — env vars reference
   - `setup.md` — setup guide
   - `pairing.md` — device pairing

## Critical config gotchas (memorize these)
- `additionalProperties: false` on many config sections — ONE invalid key silently breaks the ENTIRE section
- Valid keys under `tools`: profile, allow, alsoAllow, deny, byProvider, web, media, links, message, agentToAgent, elevated, exec, subagents, sandbox
- `allowAgents` only valid on per-agent `agents.list[].subagents`, NOT on `agents.defaults.subagents`
- Non-loopback gateway bind REQUIRES auth token/password
- `commands.restart: true` required for /restart command
- `commands.config: true` required for /config command
- Tool filtering order: profile → provider profile → global allow/deny → provider allow/deny → agent allow/deny → agent provider → sandbox → subagent
- Each level can ONLY further restrict, never grant back denied tools
