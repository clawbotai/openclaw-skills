# structure-standard

Unified structure enforcement for OpenClaw skills and workspaces. Validates project layouts, scaffolds new projects from templates, audits filesystem organization, and enforces permissions.

## What It Does

- **Validates** skill and project directory structures against defined standards
- **Scaffolds** new projects (Node, Python, Go, ML, Skill) from manifest templates
- **Audits** workspace filesystem layout for compliance
- **Cleans** stale files (logs, caches, temp files) with configurable age thresholds
- **Enforces** file permissions and ownership

## Quick Start

### Validate a skill structure

```bash
bash scripts/validate-structure.sh <path-to-skill> skill
```

### Scaffold a new Node project

```bash
bash scripts/scaffold.sh my-project node-app
```

### Audit workspace filesystem

```bash
bash scripts/audit-filesystem.sh /path/to/workspace
```

### Clean stale files

```bash
bash scripts/cleanup-stale.sh /path/to/workspace --days 30
```

### Enforce permissions

```bash
bash scripts/enforce-permissions.sh /path/to/workspace
```

## Scripts

| Script | Purpose |
|--------|---------|
| `validate-structure.sh` | Check project/skill structure against standards |
| `scaffold.sh` | Generate new projects from templates |
| `audit-filesystem.sh` | Audit filesystem layout compliance |
| `cleanup-stale.sh` | Remove stale logs, caches, temp files |
| `enforce-permissions.sh` | Set correct file/directory permissions |

## Templates

Templates live in `templates/` with manifest files defining the structure:

- `skill/` — OpenClaw skill skeleton
- `node-app/` — Node.js application
- `go-app/` — Go application
- `ml-project/` — ML/data science project

## Requirements

- Bash 4+
- macOS or Linux
- Standard Unix tools (find, stat, chmod)

## License

MIT
