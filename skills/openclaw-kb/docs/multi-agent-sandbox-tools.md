# Multi-Agent Sandbox & Tools

## Tool Filtering Precedence (critical)
1. Tool profile (tools.profile or agents.list[].tools.profile)
2. Provider tool profile (tools.byProvider[provider].profile)
3. Global tool policy (tools.allow / tools.deny)
4. Provider tool policy (tools.byProvider[provider].allow/deny)
5. Agent-specific tool policy (agents.list[].tools.allow/deny)
6. Agent provider policy (agents.list[].tools.byProvider[provider].allow/deny)
7. Sandbox tool policy (tools.sandbox.tools)
8. Subagent tool policy (tools.subagents.tools)

**Each level can ONLY further restrict — cannot grant back denied tools.**

## Tool groups (shorthands)
- group:runtime → exec, bash, process
- group:fs → read, write, edit, apply_patch
- group:sessions → sessions_list/history/send/spawn, session_status
- group:memory → memory_search, memory_get
- group:web → web_search, web_fetch
- group:ui → browser, canvas
- group:automation → cron, gateway
- group:messaging → message
- group:nodes → nodes
- group:openclaw → all built-in tools

## Sandbox Config Precedence
Agent-specific overrides global for: mode, scope, workspaceRoot, workspaceAccess, docker.*, browser.*, prune.*

## Elevated Mode
- tools.elevated is global baseline (sender-based allowlist)
- agents.list[].tools.elevated can only further restrict
- NOT configurable to grant back elevated access per agent

## Common Pitfall: "non-main"
Based on session.mainKey (default "main"), not agent id. Group/channel sessions are always non-main → will be sandboxed.
