# Gateway Runbook

## 5-minute local startup
1. Install OpenClaw
2. Run `openclaw onboard`
3. Start gateway

## Runtime model
- One always-on process for routing, control plane, and channel connections.
- Single multiplexed port for: WebSocket control/RPC, HTTP APIs (OpenAI-compatible, Responses, tools invoke), Control UI and hooks.
- Default bind mode: loopback.
- Auth required by default (gateway.auth.token / gateway.auth.password, or OPENCLAW_GATEWAY_TOKEN / OPENCLAW_GATEWAY_PASSWORD).

### Port and bind precedence
- Gateway port: --port → OPENCLAW_GATEWAY_PORT → gateway.port → 18789
- Bind mode: CLI/override → gateway.bind → loopback

### Hot reload modes
- off: No config reload
- hot: Apply only hot-safe changes
- restart: Restart on reload-required changes
- hybrid (default): Hot-apply when safe, restart when required

## Operator command set
```
openclaw gateway status
openclaw gateway status --deep
openclaw gateway status --json
openclaw gateway install
openclaw gateway restart
openclaw gateway stop
openclaw logs --follow
openclaw doctor
```

## Remote access
Preferred: Tailscale/VPN.
Fallback: SSH tunnel: `ssh -N -L 18789:127.0.0.1:18789 user@host`

## Supervision and service lifecycle
- macOS (launchd): `openclaw gateway install` → LaunchAgent labels are `ai.openclaw.gateway` (default) or `ai.openclaw.<profile>` (named profile)
- Linux (systemd user): `openclaw gateway install` → `systemctl --user enable --now openclaw-gateway[-<profile>].service`
- Linux (system service): system unit for multi-user/always-on hosts

## Multiple gateways on one host
Checklist per instance:
- Unique gateway.port
- Unique OPENCLAW_CONFIG_PATH
- Unique OPENCLAW_STATE_DIR
- Unique agents.defaults.workspace

## Protocol quick reference
- First client frame must be connect
- Gateway returns hello-ok snapshot
- Requests: req(method, params) → res(ok/payload|error)
- Common events: connect.challenge, agent, chat, presence, tick, health, heartbeat, shutdown
- Agent runs are two-stage: immediate accepted ack → final completion response

## Common failure signatures
- `refusing to bind gateway ... without auth` → Non-loopback bind without token/password
- `another gateway instance is already listening / EADDRINUSE` → Port conflict
- `Gateway start blocked: set gateway.mode=local` → Config set to remote mode
- `unauthorized during connect` → Auth mismatch
