# Sandboxing

OpenClaw can run tools inside Docker containers to reduce blast radius. Optional, controlled by agents.defaults.sandbox or agents.list[].sandbox.

## What gets sandboxed
- Tool execution (exec, read, write, edit, apply_patch, process, etc.)
- Optional sandboxed browser

**Not sandboxed:** Gateway process itself, tools.elevated (always host), tools when sandbox is off.

## Modes (agents.defaults.sandbox.mode)
- **off**: no sandboxing
- **non-main**: sandbox only non-main sessions (based on session.mainKey, not agent id)
- **all**: every session runs in a sandbox

Note: Group/channel sessions count as non-main and will be sandboxed under "non-main" mode.

## Scope (agents.defaults.sandbox.scope)
- **session** (default): one container per session
- **agent**: one container per agent
- **shared**: one container shared by all sandboxed sessions

## Workspace access (agents.defaults.sandbox.workspaceAccess)
- **none** (default): sandbox workspace under ~/.openclaw/sandboxes
- **ro**: agent workspace mounted read-only at /agent
- **rw**: agent workspace mounted read/write at /workspace

## Custom bind mounts
- docker.binds: host:container:mode format
- browser.binds: replaces docker.binds for browser container when set
- Global and per-agent binds are merged (not replaced)

## Images + setup
- Default image: openclaw-sandbox:bookworm-slim
- Build: `scripts/sandbox-setup.sh`
- setupCommand: runs once after container creation (needs network + writable root + root user)
- Default network: none

## Tool policy + escape hatches
- Tool allow/deny applies before sandbox rules
- tools.elevated is explicit host escape hatch
- Debug: `openclaw sandbox explain`
