# Filesystem Standard

A system-level filesystem standard for OpenClaw deployments. Defines canonical directory layout, permission model, cleanup rules, and navigation conventions for AI autonomous systems.

Complements `project-structure` (which handles individual skill/project layout) by addressing the **system-level** filesystem.

---

## A. AI Autonomous System Filesystem Theory

### Convention Over Configuration
AI agents make thousands of micro-decisions per session. Every predictable path eliminates a decision. A standardized filesystem means the agent never wastes tokens figuring out *where* something is — it just knows.

### Self-Describing Filesystems
Every directory should declare its purpose. `_meta.json` for machine parsing, `README.md` for human/agent reading. If a directory has >3 files, it needs a manifest or README. An agent landing in any directory should understand its purpose within one file read.

### Separation of Concerns
Four distinct zones, never mixed:

| Zone | Path | Owner | Volatility |
|------|------|-------|------------|
| **System** | `~/.openclaw/` | OpenClaw daemon | Low (config changes rarely) |
| **Workspace** | `~/openclaw/workspace/` | Agent | Medium (daily changes) |
| **Credentials** | `~/.openclaw/credentials/` | Daemon | Very low (locked down) |
| **Ephemeral** | `~/.openclaw/sandbox/`, `subagents/` | Auto-managed | High (auto-cleanup) |

### Principle of Least Surprise
- Config lives in dotfiles. Work lives in workspace. Scripts live in scripts/.
- No loose files in $HOME. Everything has a home.
- Naming is predictable: kebab-case for directories, UPPER_CASE.md for workspace-level docs.

### XDG Influence
OpenClaw follows XDG spirit: `~/.openclaw/` is analogous to `~/.config/` + `~/.local/`. Config, data, cache, and runtime state are separated within it. We don't use XDG paths directly because OpenClaw is a self-contained system, but the philosophy applies.

### Immutable Infrastructure Principles
- System config (`~/.openclaw/`) should be reproducible from a known state
- Workspace is version-controlled — any state can be recovered via git
- Ephemeral directories (sandbox, subagents) are disposable by design
- Config backups: max 1 — if you need more history, that's what git is for

---

## B. OpenClaw Standard Filesystem Layout

```
$HOME/
├── .openclaw/                    # SYSTEM — managed by OpenClaw daemon
│   ├── config.json               # Gateway configuration
│   ├── openclaw.json             # Main config (keep max 1 .bak)
│   ├── agents/                   # Agent definitions (main, provider-specific)
│   ├── canvas/                   # Canvas data
│   ├── completions/              # Shell completions
│   ├── credentials/              # Secrets — 700/600 permissions
│   ├── cron/                     # Scheduled jobs and run history
│   ├── devices/                  # Paired devices
│   ├── identity/                 # Agent identity keys
│   ├── logs/                     # Rotated logs (max 7 days)
│   ├── memory/                   # System-level memory
│   ├── sandbox/                  # Ephemeral sandboxed execution
│   ├── skills/                   # System-level skills
│   ├── subagents/                # Session data (auto-cleanup 24h)
│   └── workspace-*/              # Provider-specific workspaces
│
├── openclaw/workspace/           # WORKSPACE — agent's working directory
│   ├── .env                      # Gateway connection URL (gitignored)
│   ├── .git/                     # Version control
│   ├── .gitignore                # Standard ignores (see section E)
│   ├── .clawhub/                 # ClawHub sync metadata
│   ├── AGENTS.md                 # Agent behavior rules
│   ├── SOUL.md                   # Agent personality
│   ├── IDENTITY.md               # Agent identity
│   ├── USER.md                   # User information
│   ├── TOOLS.md                  # Tool-specific notes
│   ├── HEARTBEAT.md              # Periodic task config
│   ├── MEMORY.md                 # Long-term memory (main session only)
│   ├── memory/                   # Daily logs (YYYY-MM-DD.md)
│   ├── skills/                   # All skills (see project-structure)
│   └── projects/                 # User projects (separate from skills)
│
├── scripts/                      # User utility scripts (not scattered in $HOME)
│   ├── clean_slate.sh
│   └── searx.sh
│
├── .venv/                        # Python virtual environment
├── .ssh/                         # SSH keys (standard)
├── .ollama/                      # Local LLM runtime
├── .colima/                      # Container runtime config
└── .docker/                      # Docker config
```

### What Does NOT Belong in $HOME Root
- Stale log files (`openclaw.log`) → should be in `~/.openclaw/logs/`
- Loose scripts (`clean_slate.sh`, `searx.sh`) → move to `~/scripts/`
- Old backup directories (`Clawaibot_Backup/`) → archive or remove
- Orphaned repos (`skills/` with 2661 items) → remove after confirming not needed
- Stale inspection dirs (`skill-inspection/`) → remove
- Tarball backups (`*_Pristine_State.tar.gz`) → archive or remove
- Ollama model configs (`Modelfile`) → move to `~/.ollama/` or `~/scripts/`

---

## C. Permission Standards

| Path | Type | Mode | Rationale |
|------|------|------|-----------|
| `~/.openclaw/credentials/` | dir | `700` | Secrets — owner only |
| `~/.openclaw/credentials/*` | file | `600` | Secrets — owner only |
| `~/.openclaw/openclaw.json` | file | `600` | Contains sensitive config |
| `~/.openclaw/config.json` | file | `644` | Gateway config (non-secret) |
| `workspace/.env` | file | `644` | Just gateway URL, non-secret |
| `*.sh` | file | `755` | Executable scripts |
| `*.py` (with shebang) | file | `755` | Executable scripts |
| All other files | file | `644` | Standard read |
| All directories | dir | `755` | Standard traverse |
| `~/.openclaw/credentials/` | dir | `700` | Exception — restricted |

### Quick Rule
- **Secrets**: 700/600
- **Scripts**: 755
- **Everything else**: 755 (dirs) / 644 (files)

---

## D. Cleanup Rules

| Target | Rule | Automation |
|--------|------|------------|
| Config backups (`.bak*`) | Keep max 1, delete `.bak.1` through `.bak.N` | `cleanup-stale.sh` |
| System logs | Rotate, keep 7 days max | `cleanup-stale.sh` |
| Subagent sessions | Auto-cleanup after 24h | `cleanup-stale.sh` |
| `node_modules/` | NEVER in git, NEVER committed in skills | `audit-filesystem.sh` |
| Build artifacts (`dist/`, `build/`) | NEVER in git | `audit-filesystem.sh` |
| Stale task files | Cleanup after 48h if unreferenced | Manual review |
| Cron run logs | Keep 7 days | `cleanup-stale.sh` |

---

## E. .gitignore Standard

The canonical `.gitignore` for the workspace (also available as `templates/gitignore-workspace`):

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
*.swo

# OpenClaw internals
.clawhub/

# Logs
*.log

# Secrets (should never be here, but just in case)
*.key
*.pem
id_rsa*
```

---

## F. AI Navigation Optimization

### Directory Manifests
- Every directory with >3 files: include `README.md` or `_meta.json`
- Skills MUST have `_meta.json` (machine-parseable) and `SKILL.md` (agent-readable)
- Projects should have `README.md` at minimum

### Naming Conventions
| Context | Convention | Example |
|---------|-----------|---------|
| Directories | kebab-case | `deep-research-pro/` |
| Python files | snake_case | `audit_system.py` |
| Shell scripts | kebab-case or snake_case | `audit-filesystem.sh` |
| Components/Classes | PascalCase | `AgentController` |
| Workspace docs | UPPER_CASE.md | `AGENTS.md`, `SOUL.md` |
| Memory files | YYYY-MM-DD.md | `2026-02-11.md` |

### Depth Limits
- **Skills**: max 4 levels (`skills/name/scripts/lib/`)
- **Projects**: max 6 levels (standard software project depth)
- **Flat > deep**: prefer more files in a directory over more nesting

### Machine Parsing
- `_meta.json` at skill root enables automated catalog, search, dependency resolution
- Consistent structure means agents can `ls` + `cat _meta.json` to understand any skill in 2 operations

---

## G. Migration Guide

### From Current State → Standard

**Phase 1: Safe fixes (automated)**
```bash
# Run from workspace
./skills/filesystem-standard/scripts/audit-filesystem.sh        # See what's wrong
./skills/filesystem-standard/scripts/enforce-permissions.sh --apply  # Fix permissions
./skills/filesystem-standard/scripts/cleanup-stale.sh --dry-run     # Preview cleanup
./skills/filesystem-standard/scripts/cleanup-stale.sh               # Execute cleanup
```

**Phase 2: Create missing structure**
```bash
# Add .gitignore to workspace
cp skills/filesystem-standard/templates/gitignore-workspace .gitignore

# Create projects/ directory
mkdir -p projects/

# Create scripts/ directory in home
mkdir -p ~/scripts
```

**Phase 3: Relocate scattered files (requires user approval)**
```bash
# Move loose scripts to ~/scripts/
mv ~/clean_slate.sh ~/scripts/
mv ~/searx.sh ~/scripts/
mv ~/Modelfile ~/.ollama/ 2>/dev/null || mv ~/Modelfile ~/scripts/

# Remove stale log
rm ~/openclaw.log
```

**Phase 4: Handle orphaned directories (requires user decision)**
- `~/skills/` (2661 items) — old skills repo. Likely fully superseded by workspace/skills/. Recommend: verify, then `rm -rf`.
- `~/skill-inspection/` — stale inspection data. Recommend: remove.
- `~/Clawaibot_Backup/` — legacy backup. Recommend: archive to external storage or remove.
- `~/Clawaibot_Pristine_State.tar.gz` — stale tarball. Recommend: remove.

**Phase 5: Fix committed artifacts**
```bash
# Remove node_modules from any skill that has it committed
cd skills/project-cerebro
echo "node_modules/" >> .gitignore
git rm -r --cached node_modules/ 2>/dev/null
git commit -m "chore: remove committed node_modules"
```

---

## Scripts

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `scripts/audit-filesystem.sh` | Full system audit against this standard | `--fix`, `--quiet`, `--help` |
| `scripts/enforce-permissions.sh` | Set correct permissions everywhere | `--dry-run`, `--apply`, `--help` |
| `scripts/cleanup-stale.sh` | Remove stale backups, logs, sessions | `--dry-run`, `--help` |

---

## Principles Summary

1. **Everything has a home** — no loose files in $HOME
2. **Secrets are locked** — 700/600, always
3. **Git is clean** — no node_modules, no build artifacts, no .env
4. **Ephemeral is ephemeral** — auto-cleanup for sessions, logs, sandboxes
5. **Self-describing** — manifests and READMEs everywhere
6. **Convention over configuration** — predictable paths, predictable names
7. **Flat over deep** — minimize nesting, maximize discoverability
