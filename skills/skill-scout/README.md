# skill-scout

Autonomous skill intelligence and acquisition engine for OpenClaw agents.

## What It Does

Discovers, evaluates, ranks, and optionally acquires skills from the OpenClaw ecosystem (ClawHub + GitHub + awesome lists). Instead of spending 50-200K tokens building a skill from scratch, find a battle-tested one in seconds.

## Architecture

```
                    ┌─────────────┐
                    │   scout.py  │  ← Orchestrator CLI
                    │  (ranking,  │
                    │  gaps, acq) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
      ┌──────────┐  ┌───────────┐  ┌──────────┐
      │discover.py│  │evaluate.py│  │ common.py│
      │ ClawHub   │  │ 7-dim     │  │ DB, Shell│
      │ GitHub    │  │ scoring   │  │ Logging  │
      │ Awesome   │  │ AST scan  │  │          │
      └──────────┘  └───────────┘  └──────────┘
              │            │            │
              └────────────┼────────────┘
                           ▼
                    ┌──────────────┐
                    │  scout.db    │  SQLite WAL
                    │  (skills,    │
                    │  developers, │
                    │  evaluations)│
                    └──────────────┘
```

## Quick Start

```bash
cd skills/skill-scout/scripts

# 1. Bootstrap — discover skills across the ecosystem
python3 discover.py sweep --categories "calendar,email,devops,security"

# 2. Evaluate a skill
python3 evaluate.py score --slug "calendar"

# 3. Check for capability gaps
python3 scout.py gaps
```

## CLI Reference

### discover.py — Find skills

| Command | Description |
|---------|-------------|
| `discover.py clawhub --query "X" --limit N` | Search ClawHub registry |
| `discover.py github --query "X" --limit N` | Search GitHub repos |
| `discover.py awesome [--refresh]` | Parse VoltAgent awesome list |
| `discover.py developer --username "X"` | Build developer profile |
| `discover.py sweep --categories "a,b,c"` | Multi-category parallel sweep |

### evaluate.py — Score quality

| Command | Description |
|---------|-------------|
| `evaluate.py score --slug "X"` | Evaluate remote skill |
| `evaluate.py score --path /dir/` | Evaluate local skill |
| `evaluate.py batch --slugs "a,b,c"` | Batch evaluate |
| `evaluate.py security --path /dir/` | Security-only scan |
| `evaluate.py compare --slug "X" --ours "Y"` | Head-to-head comparison |

### scout.py — Orchestrate

| Command | Description |
|---------|-------------|
| `scout.py rank-developers [--min-skills N]` | Rank developers |
| `scout.py rank-skills [--category X]` | Rank skills |
| `scout.py gaps [--our-skills /path/]` | Gap analysis |
| `scout.py recommend --category "X"` | Recommend skills |
| `scout.py acquire --slug "X" [--dry-run\|--install]` | Acquire with security gates |
| `scout.py watch --add "user" [--reason "X"]` | Watch a developer |
| `scout.py watch --check` | Check watched devs |
| `scout.py watch --list` | List watch list |
| `scout.py report --type ecosystem\|developers\|gaps\|alerts` | Generate reports |
| `scout.py stats` | Database statistics |
| `scout.py prune --days N` | Remove stale records |

## Database

- **Location:** `memory/skill-scout/scout.db`
- **Mode:** SQLite WAL (concurrent reads during writes)
- **Tables:** `skills`, `developers`, `evaluations`
- **Reports:** JSON files in `memory/skill-scout/`

## Security Model

- AST-based static analysis for Python: eval, exec, os.system, subprocess(shell=True), pickle, network imports
- Regex credential detection: AWS keys, OpenAI keys, GitHub PATs, hardcoded passwords, private keys
- Critical flags block installation and cap quality tier at C
- All installations require user approval — no auto-install

## Requirements

- Python 3.9+ (stdlib only, zero pip installs)
- `clawhub` CLI (optional, for ClawHub access)
- `gh` CLI (optional, for GitHub access)
- Degrades gracefully if either CLI is missing

## Rate Limits

- GitHub API: 5,000 requests/hour (authenticated)
- ClawHub: Assumed reasonable (no documented limits)
- Circuit breaker: 3 consecutive failures → falls back to cached DB results
