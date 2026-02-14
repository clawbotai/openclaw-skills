# Skills

OpenClaw uses AgentSkills-compatible skill folders. Each skill is a directory with SKILL.md (YAML frontmatter + instructions).

## Locations and precedence
1. <workspace>/skills (highest)
2. ~/.openclaw/skills (managed/local)
3. bundled skills (lowest)
4. skills.load.extraDirs (lowest precedence)

## Format
```yaml
---
name: my-skill
description: What the skill does
metadata: {"openclaw": {"requires": {"bins": ["uv"], "env": ["API_KEY"]}, "primaryEnv": "API_KEY"}}
---
Instructions for the agent...
```

## Gating (load-time filters)
- always: true — skip all gates
- os: ["darwin", "linux", "win32"]
- requires.bins — each must exist on PATH
- requires.anyBins — at least one must exist
- requires.env — env var must exist or be in config
- requires.config — openclaw.json paths must be truthy
- primaryEnv — maps to skills.entries.<name>.apiKey

## Optional frontmatter keys
- user-invocable: true|false (default: true)
- disable-model-invocation: true|false (default: false)
- command-dispatch: tool — slash command bypasses model
- command-tool: tool name for dispatch
- homepage: URL for macOS Skills UI

## Config overrides
```json
{
  "skills": {
    "entries": {
      "my-skill": {
        "enabled": true,
        "apiKey": "KEY",
        "env": { "MY_API_KEY": "KEY" },
        "config": { "endpoint": "https://..." }
      }
    },
    "allowBundled": ["gemini", "peekaboo"]
  }
}
```

## ClawHub
- Browse: https://clawhub.com
- Install: `clawhub install <name>`
- Update: `clawhub update --all`
- Sync: `clawhub sync --all`

## Token impact
Per skill: ~97 chars + name + description + location length.

## Skills watcher
Auto-refresh when SKILL.md files change (default: enabled).

## Remote macOS nodes
Linux gateway can use macOS-only skills when a macOS node is connected with system.run allowed.
