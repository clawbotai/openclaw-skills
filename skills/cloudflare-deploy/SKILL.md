---
name: cloudflare-deploy
description: Deploy static websites and web apps to Cloudflare Pages using Python's standard library. Includes project management, deployment operations, rollback capabilities, and domain management.
---

# Cloudflare Pages Deploy

Cloudflare Pages Direct Upload is the fastest path from local files to a global CDN. No build step on their side, no git integration required — you hash files locally, upload via multipart, and the deployment goes live in seconds across 300+ edge locations.

This skill wraps the Pages API in Python stdlib-only scripts. No `wrangler`, no `node_modules`, no dependencies beyond Python 3.9+. That constraint is intentional: deploy scripts must work everywhere, including CI environments and minimal containers where installing npm is wasteful or impossible.

The API has real gotchas. File hashing determines deduplication — get it wrong and you upload everything every time. Branch semantics control which deployment is "production" vs "preview." Bindings (D1, KV, secrets) interact with Pages Functions in ways that can silently break your entire site. This skill encodes those lessons.

## Prerequisites

- Python 3.9+
- Environment variables: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`
- Token needs permissions: Cloudflare Pages (Edit), D1 (Edit), Workers Scripts (Edit) for full functionality

## Scripts

### `scripts/deploy.py` — Deploy a directory

```bash
python scripts/deploy.py <project_name> <directory> [--branch main] [--json]
```

Implements the full CF Pages Direct Upload flow:
1. Walks the directory tree and hashes every file (SHA-256, hex-encoded)
2. Sends hash manifest to CF to identify which files are already uploaded (deduplication)
3. Uploads only new/changed files via multipart POST
4. Creates deployment referencing the complete file set

**When to use:** Every deployment. This is the primary deploy mechanism.

**Branch semantics matter.** `--branch main` (or whatever your production branch is) creates a production deployment. Any other branch name creates a preview deployment with its own URL. Preview deployments don't affect your production domain.

### `scripts/projects.py` — Project management

```bash
python scripts/projects.py list                          # All projects in account
python scripts/projects.py create <name> [--production-branch main]
python scripts/projects.py info <name>                   # Config, domains, latest deploy
python scripts/projects.py delete <name>                 # Permanent — removes all deployments
python scripts/projects.py domains <name>                # List custom domains
python scripts/projects.py add-domain <name> <domain>    # Add custom domain
```

**When to use:** Project setup (once), domain management (rare), debugging (check `info` to see current state).

### `scripts/status.py` — Deployment status & rollback

```bash
python scripts/status.py list <project>                        # Recent deployments
python scripts/status.py info <project> <deployment_id>        # Single deployment details
python scripts/status.py logs <project> <deployment_id>        # Build/deploy logs
python scripts/status.py rollback <project> <deployment_id>    # Promote old deployment to production
```

**When to use:** After every deploy (verify), during incidents (find good deployment to rollback to), debugging (check logs for failed deploys).

**Rollback is instant.** CF Pages rollback just re-promotes an older deployment — no rebuild, no re-upload. Know your last-known-good deployment ID.

## Deployment Workflow

```
build → deploy → verify → decide
                            │
                    ┌───────┴───────┐
                    │               │
                 healthy?        broken?
                    │               │
                  done         rollback → investigate
```

### Step by step:

1. **Build** — Generate your static site locally. Run tests. Verify the output directory looks right.
2. **Deploy** — `python scripts/deploy.py <project> <directory> --branch main`
3. **Verify** — Hit the production URL. Check key pages. If you have Pages Functions, test those endpoints specifically.
4. **Decide** — If broken, rollback immediately: `python scripts/status.py rollback <project> <last_good_id>`

### Rollback decision tree:

| Symptom | Action |
|---|---|
| Site loads but content wrong | Rollback to previous deployment |
| 404 on all pages | Check deploy output — files may not have uploaded. Redeploy. |
| 405 on Functions endpoints | Binding misconfiguration. See "The Binding Trap" below. |
| Site loads but slow/stale | Cache issue. Purge via CF dashboard or API. |
| Custom domain not resolving | DNS issue, not deployment. Check DNS records. |

## DNS & Domains

Custom domains on Pages require:
- Domain's DNS managed by Cloudflare (easiest) OR external DNS with CNAME
- A CNAME record pointing your domain to `<project>.pages.dev`

**For Cloudflare-managed DNS:**
```
Type: CNAME
Name: @ (or subdomain)
Target: <project>.pages.dev
Proxy: Yes (orange cloud)
```

**For subdomains:**
```
Type: CNAME
Name: shop
Target: <project>.pages.dev
```

SSL is automatic. Cloudflare provisions a certificate for your custom domain. No action needed, but first-time setup can take a few minutes.

**Common DNS gotcha:** If you already have an A record for `@`, you can't add a CNAME for `@` (CNAME at zone apex conflicts with other records). Use Cloudflare's DNS — they support CNAME flattening at the apex.

## Secrets & Bindings

Pages projects can bind to Cloudflare services: D1 databases, KV namespaces, R2 buckets, environment variables, and secrets.

### Environment Variables & Secrets

Set via dashboard or API. Available to Pages Functions at runtime via `env` parameter.

- **Environment variables:** Non-sensitive config. Visible in dashboard.
- **Secrets:** Sensitive values. Write-only in dashboard (can't read back). Available as `env.SECRET_NAME` in Functions.
- **Per-environment:** Production and Preview can have different values.

### Bindings (D1, KV, R2)

Bindings connect your Pages Functions to Cloudflare services. Configure via dashboard or `wrangler.toml`.

**The `wrangler.toml` relationship:** If your project has a `wrangler.toml` with `[[d1_databases]]` or `[[kv_namespaces]]`, `wrangler pages deploy` reads it. Direct API upload (this skill) does NOT read `wrangler.toml` — bindings must be set via dashboard or API separately.

### Binding configuration via API:

Bindings are set on the project, not per-deployment. Update them via:
```
PATCH /accounts/{account_id}/pages/projects/{project_name}
```

With body containing `deployment_configs.production.d1_databases`, `kv_namespaces`, etc.

## Anti-Patterns

### The Dirty Deploy

**Pattern:** Deploy directly from a working directory with uncommitted changes, untested code, or stale build output.

**Reality:** You can't rollback to "whatever was on my laptop Tuesday." You can't reproduce the deployment. You can't audit what changed. When it breaks at 2am, you're guessing.

**Fix:** Always deploy from a clean build. Commit first. Tag the commit. Build from the tag. Record the commit hash with the deployment: `memory.py remember "[cloudflare-deploy] Deployed {project} at {url}, commit {hash}"`.

### The Binding Trap

**Pattern:** Add a D1 or KV binding to a Pages project, and suddenly all Pages Functions return 405 Method Not Allowed — even endpoints that don't use the binding.

**Reality:** This is a known Cloudflare behavior. Adding certain bindings can change how Functions are routed or compiled. The 405 appears on all Function routes, not just new ones. Old deployments that worked before also start returning 405 after the binding is added to the project config.

**Fix:** Test bindings in a preview deployment first. If you hit 405: (1) check `wrangler pages functions tail` for errors, (2) try removing the binding and redeploying to confirm it's the cause, (3) redeploy without `wrangler.toml` if using Direct Upload, (4) contact CF support if it persists — this is a platform issue, not your code.

### The Rollback Amnesia

**Pattern:** Something breaks in production. You need to rollback. You have no idea which deployment was the last good one.

**Reality:** `python scripts/status.py list <project>` shows recent deployments, but they're identified by ID and timestamp — not by "this was the one that worked." If you deployed 5 times today, good luck guessing.

**Fix:** Log every deployment with its commit hash and purpose. Use the memory protocol: `memory.py remember "[cloudflare-deploy] Deployed torr-statics at https://torr-statics.pages.dev, commit abc123"`. When you need to rollback, check memory for the last known-good deploy, then: `python scripts/status.py rollback <project> <deployment_id>`.

## Troubleshooting

### 405 on Pages Functions

Most common cause: binding misconfiguration. See "The Binding Trap" above.

Other causes:
- Function file not in `functions/` directory at project root
- Function filename doesn't match expected route (`functions/api/orders.ts` → `/api/orders`)
- TypeScript compilation error (check build logs)
- Function exceeds size limit (1MB compressed)

### CORS Issues

Pages Functions need explicit CORS headers. Cloudflare doesn't add them for you.

```js
// In your Function
return new Response(body, {
  headers: {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  }
});
```

Handle `OPTIONS` preflight requests explicitly — don't let them fall through to your handler logic.

### Stale Cache

Cloudflare caches aggressively. After deploy:
- HTML is typically not cached (but check your Cache-Control headers)
- Static assets (JS, CSS, images) are cached by content hash in the URL
- If using plain filenames without hashes, add `Cache-Control: no-cache` or purge via API

### Upload Failures

- **413 Request Entity Too Large:** Individual file exceeds 25MB limit. Compress or split.
- **429 Too Many Requests:** Rate limited. Back off and retry. The deploy script handles this automatically.
- **Authentication errors:** Token expired or lacks Pages permission. Regenerate in CF dashboard.

## Security

- Never log or print `CLOUDFLARE_API_TOKEN`
- All scripts use Python stdlib only — no supply chain risk from third-party packages
- Structured JSON output on `--json` flag or errors
- All scripts use exception-based error handling with `sys.exit()` only at CLI boundary

## Cross-Skill Integration

### Safety Gate
- **Before deploy**: `guardrails.py check --action deploy_site --target {project_name}`
- **Before secret changes**: `guardrails.py check --action modify_secrets --target {project_name}` (T4)

### Memory Protocol
- **After deploy**: `memory.py remember "[cloudflare-deploy] Deployed {project} at {url}, commit {hash}"`
- **After rollback**: `memory.py remember "[cloudflare-deploy] Rolled back {project}: {reason}" --importance 0.9`

### Connected Skills
- **web-builder** → builds the site, cloudflare-deploy pushes it live
- **devops** → CI/CD pipeline triggers deploy
- **security** → pre-deploy security check

---

## Quick Reference Card

```
# Deploy
python scripts/deploy.py <project> <dir> --branch main

# List deployments
python scripts/status.py list <project>

# Rollback
python scripts/status.py rollback <project> <deployment_id>

# Project info
python scripts/projects.py info <project>

# Add custom domain
python scripts/projects.py add-domain <project> <domain>

# DNS for custom domain
CNAME → <project>.pages.dev (proxied)

# Env vars: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID
# Python 3.9+, stdlib only, no dependencies
```

| Problem | First Check |
|---|---|
| 405 on Functions | Binding misconfiguration |
| Stale content | Cache purge or content-hash filenames |
| Domain not working | DNS CNAME to `<project>.pages.dev` |
| Upload fails | File size < 25MB, token permissions |
| Can't rollback | Check `status.py list`, find last-good ID |
