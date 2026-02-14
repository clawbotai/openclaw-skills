# Forge Skill

Meta-skill for code generation and skill composition.

## Trigger

Two modes based on invocation pattern:

### Mode 1: Code Generation
> `forge "build a REST API for ..."`

Single quoted/described prompt → delegates to Gemini via Antigravity Forge Daemon.

### Mode 2: Skill Application
> `forge <operator-skill> <target-skill>`
> `forge lifecycle devops`
> `forge reflect email-manager`

Two skill names → applies the operator skill's methodology against the target skill.

---

## Mode 1: Code Generation (Gemini Forge)

### 1. Ensure the daemon is running

```bash
curl -sf http://localhost:2468/health || \
  (cd /Users/clawai/openclaw/workspace/antigravity-forge-daemon && \
   node dist/index.js --http &)
```

Wait up to 5s for `/health` to return `{"status":"ok"}`.

### 2. Gather context

Before submitting, gather relevant workspace context:
- File tree of the target directory (`find . -type f | head -200`)
- Key files the user references or that are relevant
- Any constraints from USER.md (Python 3.9, stdlib-only, etc.)

Pack into `localContext` (keep under ~30KB).

### 3. Submit → Poll → Pull → Apply

Use the daemon's 3 MCP tools via HTTP at `http://localhost:2468/mcp`:

1. **submit_forge_job** — `{ "prompt": "<user prompt>", "localContext": "<context>" }` → get `jobId`
2. **poll_job_status** — every 5s until `COMPLETED` or `FAILED`
3. **pull_integration_manifest** — get the `IntegrationManifest`

### 4. Apply the manifest

Present summary first, then:
- `CREATE` / `UPDATE`: Write files with `write` tool
- `DELETE`: Use `trash` (not `rm`)
- Run each `requiredCommands` entry

---

## Mode 2: Skill Application (Skill × Skill)

### Detection

If the user provides two tokens that match skill names/aliases in `<available_skills>`, this is Mode 2.

Common operator skills and what they do:

| Operator | Action |
|----------|--------|
| `lifecycle` | Research→Build→Reflect loop + AIOps analysis against target skill |
| `reflect` | Analyze recent usage, extract learnings, encode improvements |
| `sanity-check` | Run INTAKE/MIDPOINT/OUTPUT gates against target skill |
| `skill-scout` | Evaluate target skill quality across 7 dimensions |
| `security` | Security audit of target skill's scripts and patterns |
| `docs-engine` | Generate/improve documentation for target skill |

Any skill can be an operator — the pattern is general.

### Workflow

#### Step 1: Load the operator skill
Read the operator skill's SKILL.md to understand its methodology, phases, and outputs.

#### Step 2: Load the target skill
Read the target skill's SKILL.md plus key files:
- `scripts/` directory listing
- Any `*.py`, `*.sh`, `*.js` implementation files
- Recent error logs from `memory/skill-errors.json` if relevant

#### Step 3: Gather usage context
Read today's memory file (`memory/YYYY-MM-DD.md`) and recent files for:
- Any mentions of the target skill being used today
- Errors, corrections, or friction encountered
- Decisions made or patterns discovered

#### Step 4: Execute the operator's methodology
Follow the operator skill's process, applying it to the target:
- Use the operator's frameworks, checklists, and evaluation criteria
- Feed in the target skill's code, docs, and usage context
- Generate concrete improvements (not abstract suggestions)

#### Step 5: Apply changes
- Edit the target skill's SKILL.md, scripts, or create new files
- Show a diff summary of what changed and why
- Commit with message: `forge: apply <operator> to <target>`

#### Step 6: Report
Tell the user:
- What the operator skill's process found
- What was changed in the target skill
- Any follow-up recommendations

---

## Notes

- Daemon runs on port 2468 (HTTP mode), in-memory job store with 1h TTL
- Gemini API key inherited from OpenClaw environment
- Build daemon: `cd antigravity-forge-daemon && npm run build`
- Mode 2 doesn't use the daemon — it's pure skill-on-skill orchestration within the main session
- For heavy Mode 2 operations, consider spawning a sub-agent to avoid blocking
