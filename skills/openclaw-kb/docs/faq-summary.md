# FAQ Summary (Key Questions)

## First 60 seconds if broken
1. `openclaw status` — quick snapshot
2. `openclaw status --all` — pasteable report
3. `openclaw gateway status` — daemon + port
4. `openclaw logs --follow` — tail log
5. `openclaw doctor` — repair

## Installation
- Node >= 22 required, pnpm recommended, Bun NOT recommended
- Global: `npm i -g openclaw@latest`
- Source: `curl -fsSL https://openclaw.ai/install.sh | bash -s -- --install-method git`
- Runs on: macOS, Linux, Windows (WSL2), Raspberry Pi

## Auth options
- **Anthropic**: setup-token (from `claude setup-token`) or API key
- **OpenAI**: Codex OAuth or API key
- **Gemini**: Plugin auth (`openclaw plugins enable google-gemini-cli-auth`)
- **Local models**: LM Studio with Responses API

## Config basics
- JSON5 format at ~/.openclaw/openclaw.json
- Hot reload: hybrid mode by default
- Non-loopback bind requires auth token/password
- `openclaw doctor` validates and repairs

## Data locations
- Config: ~/.openclaw/openclaw.json
- Credentials: ~/.openclaw/credentials/
- Workspace: ~/.openclaw/workspace
- Sessions: ~/.openclaw/agents/<agentId>/sessions/
- Auth: ~/.openclaw/agents/<agentId>/agent/auth-profiles.json

## Migration
Copy ~/.openclaw + workspace → new machine → `openclaw doctor` → restart

## Memory
- Workspace files: AGENTS.md, SOUL.md, USER.md, MEMORY.md, HEARTBEAT.md
- memory_search + memory_get tools for semantic recall
- Pre-compaction memory flush saves durable notes
- LanceDB plugin available for vector memory

## Common issues
- "Model is not allowed" → add to agents.defaults.models allowlist
- HTTP 429 → rate limit, wait or add fallback
- "another gateway instance" → port conflict, stop old instance
- Config section silently failing → check for invalid keys (additionalProperties: false)
