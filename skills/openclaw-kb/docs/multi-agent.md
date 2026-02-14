# Multi-Agent Routing

Multiple isolated agents (separate workspace + agentDir + sessions), plus multiple channel accounts in one Gateway.

## What is "one agent"?
An agent has its own:
- Workspace (files, AGENTS.md/SOUL.md/USER.md)
- State directory (agentDir) for auth profiles, model registry
- Session store under ~/.openclaw/agents/<id>/sessions
- Auth profiles (per-agent, NOT shared)

## Routing rules (binding match order)
1. peer match (exact DM/group/channel id)
2. parentPeer match (thread inheritance)
3. guildId + roles (Discord)
4. guildId
5. teamId (Slack)
6. accountId exact match
7. accountId: "*" (channel-wide)
8. Default agent

## Key patterns
- **Two WhatsApps → two agents**: Bind by accountId
- **One WhatsApp, multiple people**: Bind by peer.kind: "direct" + sender E.164
- **Fast chat + Opus coding**: Different agents with different default models, bound by channel
- **Family agent**: Bound to specific WhatsApp group with mention gating and restricted tools

## Per-Agent Configuration
Each agent can override:
- sandbox (mode, scope, docker settings)
- tools (allow/deny, elevated)
- model
- identity (name, emoji, avatar)
- groupChat (mentionPatterns)

## Agent wizard
```
openclaw agents add work
openclaw agents list --bindings
```
