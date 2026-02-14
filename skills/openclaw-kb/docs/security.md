# Security

## Security audit CLI
Run `openclaw security audit` for a full scan of your configuration.

## Credential storage
- Auth profiles stored in ~/.openclaw/agents/<agentId>/agent/auth-profiles.json
- Never reuse agentDir across agents (causes auth/session collisions)

## DM access models
- **pairing** (default): Unknown senders get one-time pairing code; owner approves
- **allowlist**: Only senders in allowFrom (or paired allow store)
- **open**: Allow all inbound DMs (requires allowFrom: ["*"])
- **disabled**: Ignore all inbound DMs

## Session isolation
- dmScope controls DM grouping (main/per-peer/per-channel-peer/per-account-channel-peer)
- Without isolation, all DMs share context (can leak private info between users)
- Use per-channel-peer for multi-user setups

## Prompt injection risks
- Forwarded messages, web content, and media can contain injection attempts
- Smaller/quantized local models increase prompt-injection risk
- Security Notice wrapper on external content helps but isn't foolproof

## Sandboxing
- Docker containers reduce blast radius for tool execution
- modes: off, non-main, all
- scope: session, agent, shared
- workspaceAccess: none, ro, rw
- Elevated exec always runs on host, bypasses sandbox

## Browser control risks
- Browser tool can access any page the browser has open
- Use evaluateEnabled: false to disable JS evaluation
- Sandbox browser option available

## Per-agent access profiles
- Full access (no sandbox)
- Read-only tools + workspace
- No filesystem access (messaging only)

## Network exposure hardening
- Default: loopback bind
- Non-loopback requires auth
- Tailscale Serve for secure remote access
- SSH tunnels as fallback

## Configuration hardening
- Set dmPolicy: "pairing" (default)
- Enable sandboxing for non-main sessions
- Use tool deny lists for untrusted agents
- Keep commands.bash: false (default)
- Keep commands.config: false (default)
- Restrict tools.elevated.allowFrom

## Trust hierarchy
1. System prompt (highest trust)
2. Workspace files (AGENTS.md, SOUL.md, etc.)
3. User messages
4. External content (lowest trust — wrapped in security notices)
