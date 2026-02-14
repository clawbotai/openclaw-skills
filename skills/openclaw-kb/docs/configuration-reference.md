# Configuration Reference

Every field available in ~/.openclaw/openclaw.json. Config format is JSON5 (comments + trailing commas allowed). All fields are optional — OpenClaw uses safe defaults when omitted.

## Channels

Each channel starts automatically when its config section exists (unless enabled: false).

### DM and group access
DM policies: pairing (default), allowlist, open, disabled
Group policies: allowlist (default), open, disabled

### WhatsApp
- Runs through gateway's web channel (Baileys Web)
- Key fields: dmPolicy, allowFrom, textChunkLimit, chunkMode, mediaMaxMb, sendReadReceipts, groups, groupPolicy, groupAllowFrom
- Multi-account: channels.whatsapp.accounts.{name}

### Telegram
- Key fields: botToken, dmPolicy, allowFrom, groups, customCommands, historyLimit, replyToMode, linkPreview, streamMode, draftChunk, actions, reactionNotifications, mediaMaxMb, retry, proxy, webhookUrl
- Bot token: channels.telegram.botToken or tokenFile, TELEGRAM_BOT_TOKEN fallback

### Discord
- Key fields: token, mediaMaxMb, allowBots, actions, replyToMode, dm, guilds, historyLimit, textChunkLimit, maxLinesPerMessage, retry
- Token: channels.discord.token, DISCORD_BOT_TOKEN fallback
- Reaction modes: off, own (default), all, allowlist

### Signal
- Key fields: reactionNotifications, reactionAllowlist, historyLimit

### iMessage
- Key fields: cliPath, dbPath, remoteHost, dmPolicy, allowFrom, historyLimit, includeAttachments, mediaMaxMb, service, region
- Requires Full Disk Access to Messages DB
- Spawns imsg rpc (JSON-RPC over stdio)

### Google Chat
- Key fields: serviceAccountFile, audienceType, audience, webhookPath, botUser, dm, groupPolicy, groups, actions, typingIndicator, mediaMaxMb

### Slack
- Key fields: botToken, appToken, dm, channels, historyLimit, allowBots, reactionNotifications, replyToMode, thread, actions, slashCommand, textChunkLimit, mediaMaxMb
- Socket mode: botToken + appToken; HTTP mode: botToken + signingSecret

### Mattermost
- Plugin-only: `openclaw plugins install @openclaw/mattermost`
- Chat modes: oncall (default), onmessage, onchar

### Multi-account (all channels)
- accountId per login, routed to different agents via bindings

### Group chat mention gating
- Metadata mentions + text patterns (agents.list[].groupChat.mentionPatterns)
- Self-chat mode: include own number in allowFrom

### Commands
```json
{
  "commands": {
    "native": "auto",
    "text": true,
    "bash": false,
    "config": false,
    "debug": false,
    "restart": false,
    "allowFrom": {},
    "useAccessGroups": true
  }
}
```

## Agent defaults

### agents.defaults.workspace
Default: ~/.openclaw/workspace

### agents.defaults.model
```json
{
  "agents": {
    "defaults": {
      "models": {
        "anthropic/claude-opus-4-6": { "alias": "opus" }
      },
      "model": {
        "primary": "anthropic/claude-opus-4-6",
        "fallbacks": ["minimax/MiniMax-M2.1"]
      },
      "imageModel": {
        "primary": "openrouter/qwen/qwen-2.5-vl-72b-instruct:free"
      },
      "thinkingDefault": "low",
      "verboseDefault": "off",
      "elevatedDefault": "on",
      "timeoutSeconds": 600,
      "maxConcurrent": 3
    }
  }
}
```

Built-in alias shorthands:
- opus → anthropic/claude-opus-4-6
- sonnet → anthropic/claude-sonnet-4-5
- gpt → openai/gpt-5.2
- gpt-mini → openai/gpt-5-mini
- gemini → google/gemini-3-pro-preview
- gemini-flash → google/gemini-3-flash-preview

### agents.defaults.heartbeat
```json
{
  "heartbeat": {
    "every": "30m",
    "model": "openai/gpt-5.2-mini",
    "session": "main",
    "target": "last",
    "prompt": "Read HEARTBEAT.md if it exists..."
  }
}
```

### agents.defaults.compaction
- mode: default | safeguard (chunked summarization)
- memoryFlush: silent agentic turn before auto-compaction

### agents.defaults.contextPruning
- mode: off | cache-ttl
- Prunes old tool results from in-memory context (doesn't modify JSONL)

### agents.defaults.sandbox
```json
{
  "sandbox": {
    "mode": "non-main",
    "scope": "agent",
    "workspaceAccess": "none",
    "docker": {
      "image": "openclaw-sandbox:bookworm-slim",
      "network": "none",
      "setupCommand": "apt-get update && apt-get install -y git curl jq"
    }
  }
}
```

### agents.list (per-agent overrides)
- id, default, name, workspace, agentDir, model, identity, groupChat, sandbox, subagents, tools
- subagents.allowAgents: allowlist of agent ids for sessions_spawn (["*"] = any)

## Multi-agent routing
```json
{
  "bindings": [
    { "agentId": "home", "match": { "channel": "whatsapp", "accountId": "personal" } },
    { "agentId": "work", "match": { "channel": "whatsapp", "accountId": "biz" } }
  ]
}
```

Binding match order: peer → guildId → teamId → accountId (exact) → accountId "*" → default agent

## Session
- dmScope: main | per-peer | per-channel-peer | per-account-channel-peer
- identityLinks: map canonical ids to provider-prefixed peers
- reset: daily (atHour) | idle (idleMinutes)
- resetByType: per direct/group/thread overrides
- sendPolicy: deny rules by channel/chatType/keyPrefix

## Messages
- responsePrefix, ackReaction, queue (steer/followup/collect/interrupt), inbound debounce
- TTS: auto (off/always/inbound/tagged), provider (elevenlabs/openai)

## Tools

### Tool profiles
- minimal: session_status only
- coding: group:fs, group:runtime, group:sessions, group:memory, image
- messaging: group:messaging + session tools
- full: no restriction

### Tool groups
- group:runtime → exec, process
- group:fs → read, write, edit, apply_patch
- group:sessions → sessions_list/history/send/spawn, session_status
- group:memory → memory_search, memory_get
- group:web → web_search, web_fetch
- group:ui → browser, canvas
- group:automation → cron, gateway
- group:messaging → message
- group:nodes → nodes

### tools.elevated
```json
{
  "tools": {
    "elevated": {
      "enabled": true,
      "allowFrom": {
        "whatsapp": ["+15555550123"]
      }
    }
  }
}
```

### tools.web
- search: apiKey (BRAVE_API_KEY), maxResults, timeoutSeconds, cacheTtlMinutes
- fetch: maxChars, timeoutSeconds, cacheTtlMinutes

### tools.media
- audio: models (openai whisper, CLI), scope rules
- video: models (google gemini)

## Custom providers
```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "custom-proxy": {
        "baseUrl": "http://localhost:4000/v1",
        "apiKey": "KEY",
        "api": "openai-completions",
        "models": [{ "id": "llama-3.1-8b", "name": "Llama 3.1 8B" }]
      }
    }
  }
}
```

Supported APIs: openai-completions, openai-responses, anthropic-messages, google-generative-ai

## Skills config
```json
{
  "skills": {
    "allowBundled": ["gemini", "peekaboo"],
    "load": { "extraDirs": ["~/Projects/agent-scripts/skills"] },
    "entries": {
      "nano-banana-pro": { "apiKey": "KEY", "env": { "GEMINI_API_KEY": "KEY" } },
      "sag": { "enabled": false }
    }
  }
}
```

## Plugins config
```json
{
  "plugins": {
    "enabled": true,
    "allow": ["voice-call"],
    "deny": [],
    "load": { "paths": ["~/Projects/oss/voice-call-extension"] },
    "entries": { "voice-call": { "enabled": true, "config": { "provider": "twilio" } } }
  }
}
```

## Browser
```json
{
  "browser": {
    "enabled": true,
    "evaluateEnabled": true,
    "defaultProfile": "chrome",
    "profiles": {
      "openclaw": { "cdpPort": 18800 },
      "remote": { "cdpUrl": "http://10.0.0.42:9222" }
    }
  }
}
```

## Gateway
```json
{
  "gateway": {
    "mode": "local",
    "port": 18789,
    "bind": "loopback",
    "auth": { "mode": "token", "token": "your-token" },
    "tailscale": { "mode": "off" },
    "controlUi": { "enabled": true, "basePath": "/openclaw" }
  }
}
```

## Hooks
- POST /hooks/wake → { text, mode }
- POST /hooks/agent → { message, agentId, sessionKey, deliver, channel }
- Gmail integration with Pub/Sub

## Canvas host
- Serves agent-editable HTML/CSS/JS at /__openclaw__/canvas/
- A2UI at /__openclaw__/a2ui/

## Discovery
- mDNS: minimal (default) | full | off
- Wide-area DNS-SD
