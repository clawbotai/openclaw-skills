# Forge Skill

Meta-skill for code generation and skill composition. Both modes delegate to Gemini via the Antigravity Forge Daemon.

## Trigger

Two modes based on invocation pattern:

- **Mode 1:** `forge "build a REST API for ..."` — freeform code generation
- **Mode 2:** `forge lifecycle devops` — apply one skill's methodology against another

## CLI

```bash
# Mode 1: Code generation
python3 skills/forge/scripts/forge.py mode1 "build a webhook handler for Stripe"

# Mode 2: Skill × Skill
python3 skills/forge/scripts/forge.py mode2 lifecycle forge
python3 skills/forge/scripts/forge.py mode2 reflect email-manager
python3 skills/forge/scripts/forge.py mode2 security python-backend
```

Requires `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in environment.

Output: JSON `IntegrationManifest` to stdout.

## How It Works

### Mode 1: Code Generation

1. Takes the user's freeform prompt + today's memory as context
2. Spawns the forge daemon (stdio mode)
3. Submits a forge job via JSON-RPC
4. Polls every 5s until COMPLETED or FAILED (5 min timeout)
5. Returns the IntegrationManifest

### Mode 2: Skill × Skill

1. Reads the **operator** skill's SKILL.md + scripts (the methodology to apply)
2. Reads the **target** skill's SKILL.md + scripts (what to improve)
3. Reads today's memory for usage context
4. Packs everything into a forge job prompt: "Apply operator methodology to target, produce concrete file changes"
5. Same submit → poll → pull flow as Mode 1

Common operator skills:

| Operator | What it does to the target |
|----------|---------------------------|
| `lifecycle` | Research→Build→Reflect evolutionary analysis |
| `reflect` | Extract learnings from usage, encode improvements |
| `sanity-check` | Run verification gates |
| `security` | Security audit scripts and patterns |
| `docs-engine` | Generate/improve documentation |

Any skill can be an operator — the pattern is general.

## Applying the Manifest

The returned `IntegrationManifest` contains:

```json
{
  "architecturalSummary": "What was done and why",
  "operations": [
    { "path": "SKILL.md", "action": "UPDATE", "content": "...", "rationale": "..." },
    { "path": "scripts/new.py", "action": "CREATE", "content": "...", "rationale": "..." }
  ],
  "requiredCommands": ["python3 -m compileall scripts/"]
}
```

After reviewing with the user:
- `CREATE` / `UPDATE`: Write files using the `write` tool
- `DELETE`: Use `trash` (not `rm`)
- Run each command in `requiredCommands`
- Commit: `forge: apply <operator> to <target>`

## Monitor Integration

Failures are logged to `memory/forge-errors.json` with:
- Error classification (transient vs deterministic)
- Timestamps and elapsed time
- Circuit breaker: 5 failures in 5 minutes = auto-skip

## Files

```
skills/forge/
├── SKILL.md              # This file
├── SPECIFICATION.md      # Requirements doc
└── scripts/
    ├── forge.py           # Main CLI orchestrator
    └── monitor_wrapper.py # Error logging + circuit breaker
```

## Dependencies

- Antigravity Forge Daemon: `workspace/antigravity-forge-daemon/dist/index.js`
- Build: `cd antigravity-forge-daemon && npm run build`
- Env: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
