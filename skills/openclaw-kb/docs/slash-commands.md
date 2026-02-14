# Slash Commands

Commands are handled by the Gateway as standalone /... messages.

## Two systems
- **Commands**: standalone /... messages
- **Directives**: /think, /verbose, /reasoning, /elevated, /exec, /model, /queue — stripped before model sees them
  - In normal messages: inline hints, don't persist
  - In directive-only messages: persist to session

## Full command list
- /help, /commands
- /skill [input] — run a skill by name
- /status — current status + provider usage
- /allowlist — list/add/remove
- /approve allow-once|allow-always|deny
- /context [list|detail|json]
- /whoami (/id) — sender id
- /subagents list|stop|log|info|send
- /config show|get|set|unset (requires commands.config: true)
- /debug show|set|unset|reset (requires commands.debug: true)
- /usage off|tokens|full|cost
- /tts off|always|inbound|tagged|status|provider|limit|summary|audio
- /stop — abort current run
- /restart (requires commands.restart: true)
- /dock-telegram, /dock-discord, /dock-slack
- /activation mention|always (groups only)
- /send on|off|inherit
- /reset or /new [model]
- /think (aliases: /thinking, /t)
- /verbose on|full|off (/v)
- /reasoning on|off|stream (/reason)
- /elevated on|off|ask|full (/elev)
- /exec host= security= ask= node=
- /model (/models)
- /queue (debounce, cap, drop options)
- /compact [instructions]
- /bash (requires commands.bash: true + tools.elevated)

## Text-only
- ! <cmd> — host bash (one at a time)
- !poll — check output/status
- !stop — stop running bash job

## Model selection (/model)
- /model → numbered picker
- /model <n> → select by number
- /model provider/model → by name
- /model status → detailed auth/endpoint view

## Config
```json
{
  "commands": {
    "native": "auto",
    "text": true,
    "bash": false,
    "config": false,
    "debug": false,
    "restart": false,
    "allowFrom": { "*": ["user1"] }
  }
}
```
