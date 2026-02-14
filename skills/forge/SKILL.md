# Forge Skill

Invoke the Antigravity Forge Daemon to delegate heavy code-generation to Gemini.

## Trigger

User says anything like `forge "build a REST API for ..."` or `forge 'description'`.

## Workflow

### 1. Ensure the daemon is running

```bash
# Check health
curl -sf http://localhost:2468/health || \
  (cd /Users/clawai/openclaw/workspace/antigravity-forge-daemon && \
   node dist/index.js --http &)
```

Wait up to 5s for `/health` to return `{"status":"ok"}`.

### 2. Gather context

Before submitting, gather relevant workspace context for the job:
- File tree of the target directory (`find . -type f | head -200`)
- Key files the user references or that are relevant
- Any constraints from USER.md (Python 3.9, stdlib-only, etc.)

Pack this into `localContext` (keep under ~30KB).

### 3. Submit the job

```bash
curl -s http://localhost:2468/mcp -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1, "method": "tools/call",
  "params": {
    "name": "submit_forge_job",
    "arguments": {
      "prompt": "<user prompt>",
      "localContext": "<gathered context>"
    }
  }
}'
```

Extract `jobId` from the response.

### 4. Poll until complete

Poll every 5 seconds:

```bash
curl -s http://localhost:2468/mcp -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 2, "method": "tools/call",
  "params": {
    "name": "poll_job_status",
    "arguments": { "jobId": "<jobId>" }
  }
}'
```

States: `QUEUED` → `ANALYZING_CONTEXT` → `GENERATING_CODE` → `COMPLETED` or `FAILED`.

Tell the user the current state while waiting. If FAILED, show the error and stop.

### 5. Pull the manifest

```bash
curl -s http://localhost:2468/mcp -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 3, "method": "tools/call",
  "params": {
    "name": "pull_integration_manifest",
    "arguments": { "jobId": "<jobId>" }
  }
}'
```

### 6. Apply the manifest

The response contains an `IntegrationManifest`:

```json
{
  "architecturalSummary": "...",
  "operations": [
    { "path": "src/foo.ts", "action": "CREATE", "content": "...", "rationale": "..." },
    { "path": "src/bar.ts", "action": "UPDATE", "content": "...", "rationale": "..." },
    { "path": "old.ts", "action": "DELETE", "rationale": "..." }
  ],
  "requiredCommands": ["npm install", "tsc --noEmit"]
}
```

**Present the summary and operation list to the user first.** Then:

- `CREATE` / `UPDATE`: Write file content using the `write` tool
- `DELETE`: Use `trash` (not `rm`)
- Run each `requiredCommands` entry and report results

### 7. Report

Show the user:
- Architectural summary
- Files created/updated/deleted with rationales
- Command outputs (pass/fail)

## Notes

- The daemon runs in HTTP mode on port 2468 with in-memory job store (1h TTL)
- Gemini API key is in the daemon's environment (inherited from OpenClaw)
- The daemon must be built first: `cd antigravity-forge-daemon && npm run build`
- If the daemon isn't built yet, run the build before starting
