# Forge Skill

Meta-skill for code generation and skill composition. Both modes delegate to Gemini via the Antigravity Forge Daemon with **cost arbitrage guardrails** — the expensive orchestrator LLM never reads or transmits bulk code.

## Trigger

- **Mode 1:** `forge "build a REST API for ..."` — freeform code generation
- **Mode 2:** `forge lifecycle devops` — apply one skill's methodology against another

## CLI

```bash
# Mode 1: Code generation (paths are optional — defaults to workspace root)
python3 skills/forge/scripts/forge.py mode1 "build a webhook handler" ./src ./package.json

# Mode 2: Skill × Skill
python3 skills/forge/scripts/forge.py mode2 lifecycle forge
python3 skills/forge/scripts/forge.py mode2 reflect email-manager
```

Requires `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in environment.

Output: JSON with `pointer` (metadata) and `manifest` (read from disk).

## Cost Arbitrage Architecture

Three guardrails prevent the orchestrator from burning tokens on bulk code:

### G1: Zero-Context Pass-Through (Input Protection)
The `submit_forge_job` tool accepts **file paths only** — never raw content. The daemon reads files from disk using `fs/promises` before calling Gemini. The orchestrator never sees or transmits the codebase.

### G2: Token-Safe Manifest Retrieval (Output Protection)
When a job completes, the daemon writes the manifest JSON to `~/.openclaw/forge/manifest-<jobId>.json`. The `pull_integration_manifest` tool returns only a **metadata pointer**:
- `manifestPath` — local file path to the full manifest
- `architecturalSummary` — 2-sentence summary
- `filesModifiedCount` — number of operations

The orchestrator reads the manifest from disk to apply changes.

### G3: Anti-Laziness Enforcement (File Integrity Protection)
The daemon injects an aggressive system prompt forbidding truncation (`// ...rest of code`, `// unchanged`, etc.). Before marking a job COMPLETED, a **validation gate** scans all generated content against truncation regex patterns. If detected, the job is marked FAILED with a clear message.

## How It Works

### Mode 1: Code Generation

1. Takes the user's freeform prompt + optional file/directory paths
2. Spawns the forge daemon (stdio mode)
3. Sends paths (G1) → daemon reads files → calls Gemini → writes manifest to disk (G2)
4. Polls every 5s until COMPLETED or FAILED
5. Reads manifest from disk, outputs JSON

### Mode 2: Skill × Skill

1. Resolves operator and target skill directories
2. Sends operator SKILL.md path + target skill directory path + today's memory path
3. Prompt instructs Gemini to apply operator's methodology against target
4. Same submit → poll → pull → read-from-disk flow

Common operator skills:

| Operator | What it does to the target |
|----------|---------------------------|
| `lifecycle` | Research→Build→Reflect evolutionary analysis |
| `reflect` | Extract learnings from usage, encode improvements |
| `sanity-check` | Run verification gates |
| `security` | Security audit scripts and patterns |
| `docs-engine` | Generate/improve documentation |

## Applying the Manifest

After `forge.py` outputs the manifest, read it and apply:

- `CREATE` / `UPDATE`: Write files using the `write` tool
- `DELETE`: Use `trash` (not `rm`)
- Run each command in `requiredCommands`
- Commit: `forge: apply <operator> to <target>` (or descriptive message for mode1)

## Monitor Integration

Failures logged to `memory/forge-errors.json` with transient/deterministic classification.
Circuit breaker: 5 failures in 5 minutes = auto-skip.

## Files

```
skills/forge/
├── SKILL.md              # This file
├── SPECIFICATION.md      # Requirements doc
└── scripts/
    ├── forge.py           # Main CLI orchestrator (guardrail-aware)
    └── monitor_wrapper.py # Error logging + circuit breaker

~/.openclaw/forge/
└── manifest-<jobId>.json  # Output manifests (G2)
```

## Dependencies

- Antigravity Forge Daemon: `workspace/antigravity-forge-daemon/dist/index.js`
- Build: `cd antigravity-forge-daemon && npm run build`
- Env: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
