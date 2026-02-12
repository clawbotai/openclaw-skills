# Structure Standard

Unified structure enforcement — project scaffolding, validation, filesystem auditing, and workspace organization. Use for new project setup, structure validation, or workspace cleanup.

This skill combines two domains:
- **Project Structure** — Standards for organizing files and folders across all projects and skills, with validation and scaffolding tools
- **Filesystem Standard** — System-level filesystem layout, permission model, cleanup rules, and navigation conventions

---

# Part 1: Project Structure Standards

Standards for organizing files and folders across all projects and skills. Agent-first, enforceable, and pragmatic.

---

## 1. Universal Rules (All Projects)

### Required Root Files

Every project MUST have:

| File | Purpose |
|------|---------|
| `README.md` | What this is, how to run it, how to contribute |
| `.gitignore` | Language-appropriate ignores |

Every project SHOULD have:

| File | Purpose |
|------|---------|
| `LICENSE` | Legal terms (MIT default for open source) |
| `CHANGELOG.md` | Version history (Keep a Changelog format) |
| `AGENTS.md` | AI-readable project map and conventions |

### Naming Conventions

- **Folders:** `kebab-case` (e.g., `my-component/`, `data-pipeline/`)
- **Files:** `kebab-case` for most files. Language exceptions:
  - Python: `snake_case.py`
  - Go: `snake_case.go` (or single lowercase word)
  - React components: `PascalCase.tsx`
- **No spaces** in any file or folder name. Ever.
- **No uppercase** in folder names (except conventional: `README.md`, `LICENSE`, `Dockerfile`)
- **Semantic names:** `validate-order.ts` not `utils2.ts`

### Folder Structure Principles

```
project-root/
├── README.md              # Always first thing an agent reads
├── AGENTS.md              # AI navigation guide (optional but recommended)
├── src/                   # Source code (never in root)
├── tests/                 # Test files mirror src/ structure
├── docs/                  # Extended documentation
├── scripts/               # Build, deploy, utility scripts
├── config/                # Configuration files (non-secret)
├── .github/               # CI/CD workflows
└── .gitignore
```

### Anti-Patterns (Validation Script Catches These)

- ❌ `node_modules/` committed to git
- ❌ `.env` files with real secrets committed
- ❌ `dist/`, `build/`, `__pycache__/` in repo
- ❌ Files > 1MB in repo (usually wrong — use LFS or external storage)
- ❌ More than 5 files in project root (move config to `config/`)
- ❌ Generic names: `utils.js`, `helpers.py`, `misc/`, `stuff/`
- ❌ Deeply nested paths (>5 levels deep signals poor organization)

---

## 2. OpenClaw Skill Structure

### Standard Skill Anatomy

```
skill-name/
├── SKILL.md               # REQUIRED — Main skill document (agent reads this)
├── _meta.json             # REQUIRED — Machine-readable metadata
├── README.md              # Optional — Human-oriented docs (if different from SKILL.md)
├── references/            # Optional — Supporting reference docs
│   └── *.md
├── scripts/               # Optional — Executable scripts
│   └── *.sh|*.py|*.mjs
├── templates/             # Optional — File templates
│   └── */
├── data/                  # Optional — Persistent data/state
│   └── *.json|*.jsonl
├── config/                # Optional — Configuration
│   └── *.json
└── .clawhub/              # System — ClawHub sync metadata
    └── origin.json
```

### _meta.json Schema

```json
{
  "slug": "skill-name",
  "version": "1.0.0",
  "name": "Human-Readable Name",
  "description": "One-line description of what this skill does",
  "tags": ["tag1", "tag2"],
  "scripts": {
    "script-name": "scripts/script-file.sh"
  }
}
```

Required fields: `slug`, `version`, `description`.
Recommended: `name` (human-friendly display name), `tags` (for discovery).

### SKILL.md Guidelines

1. **First paragraph** = what this skill does (agent reads this to decide relevance)
2. **Use headers** = agents scan H2/H3 to find relevant sections
3. **Include examples** = concrete, copy-pasteable
4. **Aim for under 500 lines** = split into `references/*.md` for supplementary content. Master/comprehensive skills may exceed this when consolidating multiple domains — that's acceptable if well-organized with clear H2/H3 sections.
5. **No redundancy** with _meta.json = SKILL.md is prose, _meta.json is data

---

## 3. Language-Specific Templates

### Node.js Application

```
node-app/
├── README.md
├── package.json
├── package-lock.json
├── tsconfig.json           # TypeScript preferred
├── .gitignore
├── .env.example            # Template for env vars (no real values)
├── src/
│   ├── index.ts            # Entry point
│   ├── routes/             # API routes (if web server)
│   ├── services/           # Business logic
│   ├── models/             # Data models/types
│   └── utils/              # Shared utilities (with specific names!)
├── tests/
│   └── (mirrors src/)
├── scripts/
│   └── *.sh
└── config/
    └── default.json
```

### Python Application

```
python-app/
├── README.md
├── pyproject.toml          # Modern Python packaging (NOT setup.py)
├── .gitignore
├── .env.example
├── src/
│   └── app_name/           # Package directory (snake_case)
│       ├── __init__.py
│       ├── main.py         # Entry point
│       ├── routes/         # API routes (FastAPI/Flask)
│       ├── services/       # Business logic
│       ├── models/         # Pydantic models / SQLAlchemy
│       └── utils/
├── tests/
│   ├── conftest.py
│   └── (mirrors src/)
├── scripts/
└── docs/
```

### Go Application

```
go-app/
├── README.md
├── go.mod
├── go.sum
├── .gitignore
├── cmd/
│   └── app-name/
│       └── main.go         # Entry point
├── internal/               # Private packages
│   ├── handler/
│   ├── service/
│   └── model/
├── pkg/                    # Public packages (if library)
├── api/                    # API definitions (OpenAPI, protobuf)
├── scripts/
└── docs/
```

### ML/AI Project

```
ml-project/
├── README.md
├── pyproject.toml
├── .gitignore
├── AGENTS.md               # Describe model architecture, data flow
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── train.py        # Training entry point
│       ├── predict.py      # Inference entry point
│       ├── evaluate.py     # Evaluation scripts
│       ├── data/           # Data loading/processing
│       ├── models/         # Model definitions
│       ├── features/       # Feature engineering
│       └── utils/
├── notebooks/              # Jupyter notebooks (exploration only)
├── data/
│   ├── raw/                # Original immutable data (gitignored)
│   ├── processed/          # Cleaned data (gitignored)
│   └── README.md           # Describes data sources and schema
├── models/                 # Saved model artifacts (gitignored)
├── configs/
│   └── experiment.yaml
├── tests/
└── scripts/
```

### Full-Stack Web Application

```
fullstack/
├── README.md
├── package.json            # Root workspace config
├── .gitignore
├── .env.example
├── apps/
│   ├── web/                # Frontend
│   └── api/                # Backend API
├── packages/               # Shared packages
│   └── shared/
├── scripts/
├── docs/
└── infra/                  # IaC (Terraform, Docker, k8s)
```

---

## 4. AGENTS.md Specification

Every non-trivial project should include `AGENTS.md` at the root:

```markdown
# AGENTS.md

## Overview
One paragraph: what this project does.

## Architecture
Key components and how they connect.

## Key Paths
- Entry point: `src/index.ts`
- Config: `config/`
- Tests: `tests/`

## Conventions
- Language: TypeScript
- Style: ESLint + Prettier
- Tests: Vitest

## Common Tasks
- Run dev: `npm run dev`
- Run tests: `npm test`
```

---

## 5. Manifest Files

For agent navigation, complex projects should include `manifest.json`:

```json
{
  "name": "project-name",
  "type": "node-app",
  "entryPoint": "src/index.ts",
  "structure": {
    "src/routes/": "API route handlers",
    "src/services/": "Business logic"
  }
}
```

---

## 6. Configuration Management

### Environment Variables

```
.env.example    — Template with placeholder values (COMMITTED)
.env            — Real values (NEVER committed, in .gitignore)
.env.test       — Test environment (committed if no secrets)
```

### Config File Placement

- App config → `config/` directory
- CI/CD → `.github/workflows/`
- Docker → `Dockerfile` at root or `infra/docker/`
- Editor config → `.editorconfig`, `.prettierrc` at root

---

## 7. Documentation Standards

| Document | Location | Purpose |
|----------|----------|---------|
| README.md | Root | Quick start, what & why |
| AGENTS.md | Root | AI agent navigation |
| CHANGELOG.md | Root | Version history |
| CONTRIBUTING.md | Root | How to contribute |
| docs/adr/ | docs/ | Architecture Decision Records |

---

## 8. Project Validation & Scaffolding

### Validation Script

Run: `bash skills/structure-standard/scripts/validate-structure.sh <project-path> [type]`

Types: `skill`, `node-app`, `python-app`, `ml-project`, `fullstack`, `generic`

Exit codes:
- `0` — All checks passed
- `1` — Warnings only
- `2` — Errors found

### Scaffolding

Run: `bash skills/structure-standard/scripts/scaffold.sh <type> <name> [target-dir]`

Creates a new project from templates with correct structure.

### Pre-commit Integration

```yaml
- repo: local
  hooks:
    - id: validate-structure
      name: Validate project structure
      entry: bash skills/structure-standard/scripts/validate-structure.sh .
      language: system
      pass_filenames: false
```

---

## 9. Migration Guide (Projects)

1. **Audit:** Run `validate-structure.sh` to see current state
2. **Create target structure:** Use `scaffold.sh` as reference
3. **Move files incrementally:** Don't do big-bang refactors
4. **Update imports:** After each move, fix all references
5. **Validate again:** Run validation to confirm compliance
6. **Add AGENTS.md:** Document the new structure for future agents

---

# Part 2: Filesystem Standard

System-level filesystem standard for OpenClaw deployments. Defines canonical directory layout, permission model, cleanup rules, and navigation conventions.

---

## A. AI Autonomous System Filesystem Theory

### Convention Over Configuration
AI agents make thousands of micro-decisions per session. Every predictable path eliminates a decision. A standardized filesystem means the agent never wastes tokens figuring out *where* something is — it just knows.

### Self-Describing Filesystems
Every directory should declare its purpose. `_meta.json` for machine parsing, `README.md` for human/agent reading. If a directory has >3 files, it needs a manifest or README.

### Separation of Concerns
Four distinct zones, never mixed:

| Zone | Path | Owner | Volatility |
|------|------|-------|------------|
| **System** | `~/.openclaw/` | OpenClaw daemon | Low |
| **Workspace** | `~/openclaw/workspace/` | Agent | Medium |
| **Credentials** | `~/.openclaw/credentials/` | Daemon | Very low |
| **Ephemeral** | `~/.openclaw/sandbox/`, `subagents/` | Auto-managed | High |

---

## B. OpenClaw Standard Filesystem Layout

```
$HOME/
├── .openclaw/                    # SYSTEM — managed by OpenClaw daemon
│   ├── config.json               # Gateway configuration
│   ├── openclaw.json             # Main config
│   ├── agents/                   # Agent definitions
│   ├── credentials/              # Secrets — 700/600 permissions
│   ├── cron/                     # Scheduled jobs
│   ├── logs/                     # Rotated logs (max 7 days)
│   ├── sandbox/                  # Ephemeral sandboxed execution
│   ├── skills/                   # System-level skills
│   └── subagents/                # Session data (auto-cleanup 24h)
│
├── openclaw/workspace/           # WORKSPACE — agent's working directory
│   ├── .git/                     # Version control
│   ├── AGENTS.md, SOUL.md, etc.  # Workspace docs
│   ├── memory/                   # Daily logs
│   ├── skills/                   # All skills
│   └── projects/                 # User projects
```

---

## C. Permission Standards

| Path | Mode | Rationale |
|------|------|-----------|
| `~/.openclaw/credentials/` | `700` | Secrets — owner only |
| `~/.openclaw/credentials/*` | `600` | Secrets — owner only |
| `~/.openclaw/openclaw.json` | `600` | Contains sensitive config |
| `*.sh` | `755` | Executable scripts |
| All other files | `644` | Standard read |
| All directories | `755` | Standard traverse |

### Quick Rule
- **Secrets**: 700/600
- **Scripts**: 755
- **Everything else**: 755 (dirs) / 644 (files)

---

## D. Cleanup Rules

| Target | Rule | Automation |
|--------|------|------------|
| Config backups (`.bak*`) | Keep max 1 | `cleanup-stale.sh` |
| System logs | Rotate, keep 7 days max | `cleanup-stale.sh` |
| Subagent sessions | Auto-cleanup after 24h | `cleanup-stale.sh` |
| `node_modules/` | NEVER in git | `audit-filesystem.sh` |
| Build artifacts | NEVER in git | `audit-filesystem.sh` |
| Cron run logs | Keep 7 days | `cleanup-stale.sh` |

---

## E. .gitignore Standard

Canonical `.gitignore` for the workspace:

```gitignore
# Environment
.env
.env.*

# Dependencies
node_modules/
.venv/
__pycache__/
*.pyc

# Build artifacts
dist/
build/
*.egg-info/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp

# OpenClaw internals
.clawhub/

# Logs
*.log

# Secrets
*.key
*.pem
id_rsa*
```

---

## F. AI Navigation Optimization

### Naming Conventions
| Context | Convention | Example |
|---------|-----------|---------|
| Directories | kebab-case | `deep-research-pro/` |
| Python files | snake_case | `audit_system.py` |
| Shell scripts | kebab-case or snake_case | `audit-filesystem.sh` |
| Workspace docs | UPPER_CASE.md | `AGENTS.md`, `SOUL.md` |

### Depth Limits
- **Skills**: max 4 levels
- **Projects**: max 6 levels
- **Flat > deep**: prefer more files in a directory over more nesting

---

## G. Filesystem Scripts

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `scripts/audit-filesystem.sh` | Full system audit against this standard | `--fix`, `--quiet` |
| `scripts/enforce-permissions.sh` | Set correct permissions everywhere | `--dry-run`, `--apply` |
| `scripts/cleanup-stale.sh` | Remove stale backups, logs, sessions | `--dry-run` |

### Usage

```bash
# Audit the filesystem
bash skills/structure-standard/scripts/audit-filesystem.sh

# Fix permissions
bash skills/structure-standard/scripts/enforce-permissions.sh --apply

# Preview cleanup
bash skills/structure-standard/scripts/cleanup-stale.sh --dry-run

# Execute cleanup
bash skills/structure-standard/scripts/cleanup-stale.sh
```

---

## H. Migration Guide (Filesystem)

**Phase 1: Automated fixes**
```bash
bash skills/structure-standard/scripts/audit-filesystem.sh
bash skills/structure-standard/scripts/enforce-permissions.sh --apply
bash skills/structure-standard/scripts/cleanup-stale.sh --dry-run
bash skills/structure-standard/scripts/cleanup-stale.sh
```

**Phase 2: Manual cleanup (requires user approval)**
- Move loose scripts to `~/scripts/`
- Remove stale backups and orphaned directories
- Fix committed artifacts (node_modules, etc.)

---

## Quick Reference

### "Where does X go?"

| Thing | Location |
|-------|----------|
| Source code | `src/` |
| Tests | `tests/` |
| Scripts | `scripts/` |
| Documentation | `docs/` or root `.md` files |
| Config files | `config/` or root (for standard names) |
| CI/CD | `.github/workflows/` |
| Static assets | `static/` or `public/` |
| Generated output | `dist/` or `build/` (gitignored) |
| Secrets | `.env` (gitignored, ALWAYS) |

### Principles Summary

1. **Everything has a home** — no loose files
2. **Secrets are locked** — 700/600, always
3. **Git is clean** — no node_modules, no build artifacts, no .env
4. **Ephemeral is ephemeral** — auto-cleanup for sessions, logs, sandboxes
5. **Self-describing** — manifests and READMEs everywhere
6. **Convention over configuration** — predictable paths, predictable names
7. **Flat over deep** — minimize nesting, maximize discoverability
