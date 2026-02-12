---
name: cloudflare-deploy
description: Deploy static websites and web apps to Cloudflare Pages using Python's standard library. Includes project management, deployment operations, rollback capabilities, and domain management.
---

## Prerequisites

- Python 3.9+
- Environment variables: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`

## Scripts

### `scripts/deploy.py` — Deploy a directory

```bash
python scripts/deploy.py <project_name> <directory> [--branch main] [--json]
```

Implements CF Pages Direct Upload: hashes files, deduplicates, uploads via multipart, creates deployment in one request.

### `scripts/projects.py` — Project management

```bash
python scripts/projects.py list
python scripts/projects.py create <name> [--production-branch main]
python scripts/projects.py info <name>
python scripts/projects.py delete <name>
python scripts/projects.py domains <name>
python scripts/projects.py add-domain <name> <domain>
```

### `scripts/status.py` — Deployment status & rollback

```bash
python scripts/status.py list <project>
python scripts/status.py info <project> <deployment_id>
python scripts/status.py logs <project> <deployment_id>
python scripts/status.py rollback <project> <deployment_id>
```

## Security

- Never log or print `CLOUDFLARE_API_TOKEN`
- All scripts use exception-based error handling with `sys.exit()` only at CLI boundary
- Structured JSON output on `--json` flag or errors
