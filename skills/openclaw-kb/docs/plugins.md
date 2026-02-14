# Plugins (Extensions)

Plugins extend OpenClaw with commands, tools, Gateway RPC, and background services.

## Quick start
```
openclaw plugins list
openclaw plugins install @openclaw/voice-call
```

## Available official plugins
- Microsoft Teams (@openclaw/msteams)
- Memory (Core) — bundled, default
- Memory (LanceDB) — bundled, set plugins.slots.memory = "memory-lancedb"
- Voice Call (@openclaw/voice-call)
- Zalo Personal (@openclaw/zalouser)
- Matrix (@openclaw/matrix)
- Nostr (@openclaw/nostr)
- Google Antigravity OAuth (bundled, disabled)
- Gemini CLI OAuth (bundled, disabled)
- Qwen OAuth (bundled, disabled)
- Copilot Proxy (bundled, disabled)

## Plugin capabilities
- Gateway RPC methods
- Gateway HTTP handlers
- Agent tools
- CLI commands
- Background services
- Config validation
- Skills (via manifest)
- Auto-reply commands (no AI invocation)
- Channel plugins (full messaging channel)
- Provider auth flows

## Discovery & precedence
1. plugins.load.paths
2. <workspace>/.openclaw/extensions
3. ~/.openclaw/extensions
4. Bundled extensions (disabled by default)

## Config
```json
{
  "plugins": {
    "enabled": true,
    "allow": ["voice-call"],
    "deny": [],
    "entries": { "voice-call": { "enabled": true, "config": {} } },
    "slots": { "memory": "memory-core" }
  }
}
```

## Plugin slots
Exclusive categories (only one active). Use plugins.slots to select.

## CLI
```
openclaw plugins list|info|install|update|enable|disable|doctor
```

## Security
Plugins run in-process with the Gateway — treat as trusted code. Only install plugins you trust.
