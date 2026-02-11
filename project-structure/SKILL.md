# Project Structure Standards

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

**Key conventions:**
- `src/` layout always (never code in root)
- TypeScript by default (`tsconfig.json`)
- `package-lock.json` committed (reproducible builds)
- Entry point: `src/index.ts`

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

**Key conventions:**
- `pyproject.toml` over `setup.py` / `setup.cfg`
- `src/` layout (PEP 517/518 compliant)
- Virtual env NOT committed (`.venv/` in `.gitignore`)
- Type hints everywhere

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
│       │   ├── loaders.py
│       │   └── transforms.py
│       ├── models/         # Model definitions
│       ├── features/       # Feature engineering
│       └── utils/
├── notebooks/              # Jupyter notebooks (exploration only)
│   └── 01-eda.ipynb        # Numbered for ordering
├── data/
│   ├── raw/                # Original immutable data (gitignored)
│   ├── processed/          # Cleaned data (gitignored)
│   └── README.md           # Describes data sources and schema
├── models/                 # Saved model artifacts (gitignored)
├── configs/
│   └── experiment.yaml     # Hyperparameters, training config
├── tests/
└── scripts/
    ├── download-data.sh
    └── train.sh
```

**Key conventions:**
- Notebooks are for exploration, NOT production code
- Data and model artifacts gitignored (use DVC or similar)
- `data/README.md` describes schema even if data isn't committed
- Config-driven experiments (YAML/JSON, not hardcoded)

### Full-Stack Web Application

```
fullstack/
├── README.md
├── package.json            # Root workspace config
├── .gitignore
├── .env.example
├── apps/
│   ├── web/                # Frontend (SvelteKit, Next.js, etc.)
│   │   ├── src/
│   │   ├── static/
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── api/                # Backend API
│       ├── src/
│       ├── package.json
│       └── tsconfig.json
├── packages/               # Shared packages
│   └── shared/
│       ├── src/
│       └── package.json
├── scripts/
├── docs/
└── infra/                  # IaC (Terraform, Docker, k8s)
    ├── docker/
    │   └── Dockerfile
    └── terraform/
```

**Key conventions:**
- Monorepo with workspaces (npm/pnpm workspaces)
- `apps/` for deployable applications
- `packages/` for shared libraries
- `infra/` for infrastructure-as-code

---

## 4. AGENTS.md Specification

Every non-trivial project should include `AGENTS.md` at the root — a machine-readable guide for AI agents.

### Recommended Structure

```markdown
# AGENTS.md

## Overview
One paragraph: what this project does.

## Architecture
Key components and how they connect. Keep it brief.

## Key Paths
- Entry point: `src/index.ts`
- Config: `config/`
- Tests: `tests/`
- Scripts: `scripts/`

## Conventions
- Language: TypeScript
- Style: ESLint + Prettier
- Tests: Vitest
- Branching: trunk-based

## Common Tasks
- Run dev: `npm run dev`
- Run tests: `npm test`
- Deploy: `scripts/deploy.sh`
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
    "src/services/": "Business logic",
    "src/models/": "Data models and types",
    "tests/": "Test files (mirrors src/)"
  },
  "scripts": {
    "dev": "npm run dev",
    "test": "npm test",
    "build": "npm run build"
  },
  "dependencies": {
    "runtime": "Node.js 20+",
    "database": "PostgreSQL 15+"
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
- Linting → `.eslintrc`, `ruff.toml` at root

---

## 7. Documentation Standards

| Document | Location | Purpose |
|----------|----------|---------|
| README.md | Root | Quick start, what & why |
| AGENTS.md | Root | AI agent navigation |
| CHANGELOG.md | Root | Version history |
| CONTRIBUTING.md | Root | How to contribute |
| docs/adr/ | docs/ | Architecture Decision Records |
| docs/api/ | docs/ | API documentation |
| docs/guides/ | docs/ | How-to guides |

### ADR Format (docs/adr/NNN-title.md)

```markdown
# NNN. Title

**Status:** Accepted | Deprecated | Superseded by NNN
**Date:** YYYY-MM-DD

## Context
What is the issue?

## Decision
What was decided?

## Consequences
What are the trade-offs?
```

---

## 8. Enforcement

### Validation Script

Run: `bash skills/project-structure/scripts/validate-structure.sh <project-path> [type]`

Types: `skill`, `node-app`, `python-app`, `ml-project`, `fullstack`, `generic`

Exit codes:
- `0` — All checks passed
- `1` — Warnings only
- `2` — Errors found

### Scaffolding

Run: `bash skills/project-structure/scripts/scaffold.sh <type> <name> [target-dir]`

Creates a new project from templates with correct structure.

### Pre-commit Integration

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: validate-structure
      name: Validate project structure
      entry: bash skills/project-structure/scripts/validate-structure.sh .
      language: system
      pass_filenames: false
```

---

## 9. Migration Guide

### Refactoring an Existing Project

1. **Audit:** Run `validate-structure.sh` to see current state
2. **Create target structure:** Use `scaffold.sh` as reference
3. **Move files incrementally:** Don't do big-bang refactors
4. **Update imports:** After each move, fix all references
5. **Validate again:** Run validation to confirm compliance
6. **Add AGENTS.md:** Document the new structure for future agents

### Common Migrations

| From | To | Notes |
|------|----|-------|
| Flat file structure | `src/` layout | Move all source files into `src/` |
| `setup.py` | `pyproject.toml` | Use `hatch` or `setuptools` backend |
| Scattered config | `config/` dir | Consolidate, keep `.env` at root |
| No tests | `tests/` dir | Mirror `src/` structure |

---

## 10. Quick Reference

### "Where does X go?"

| Thing | Location |
|-------|----------|
| Source code | `src/` |
| Tests | `tests/` |
| Scripts | `scripts/` |
| Documentation | `docs/` or root `.md` files |
| Config files | `config/` or root (for standard names) |
| CI/CD | `.github/workflows/` |
| Docker | Root `Dockerfile` or `infra/docker/` |
| Static assets | `static/` or `public/` |
| Generated output | `dist/` or `build/` (gitignored) |
| Data files | `data/` (gitignored if large) |
| Secrets | `.env` (gitignored, ALWAYS) |
