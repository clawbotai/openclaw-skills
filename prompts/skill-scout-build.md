# BUILD PROMPT: `skill-scout` — Autonomous Skill Intelligence & Acquisition

## Your Mission

Build the complete `skill-scout` skill for **OpenClaw**, an open-source autonomous AI agent platform running on macOS ARM (Apple Silicon). This skill discovers, evaluates, ranks, and recommends high-quality skills from the OpenClaw ecosystem — saving massive development costs by finding battle-tested skills instead of building from scratch.

**Output:** 8 files in `/Users/clawai/openclaw/workspace/skills/skill-scout/`:

```
skills/skill-scout/
├── _meta.json              # Skill metadata
├── SKILL.md                # Agent instruction manual (~300 lines)
├── README.md               # Human-readable usage guide
├── CHANGELOG.md            # Keep a Changelog format, v1.0.0
├── CONTRIBUTING.md         # Dev guide for this skill
└── scripts/
    ├── discover.py         # Discovery engine (~400 LOC)
    ├── evaluate.py         # Quality scoring engine (~500 LOC)
    └── scout.py            # Unified CLI: rank, acquire, gap-analysis, report (~500 LOC)
```

---

## Platform Context

**OpenClaw** is a locally-running AI agent that uses Claude/GPT as its LLM backbone. It communicates via messaging surfaces (Signal, Telegram, Discord, webchat) and extends capabilities through "skills" — folders containing a `SKILL.md` (LLM instructions) plus supporting scripts.

**Skill ecosystem:**
- **ClawHub** (clawhub.ai): Official skill registry. 5,705+ published skills. Vector search. CLI tool `clawhub` installed at `/opt/homebrew/bin/clawhub` v0.5.0.
- **GitHub**: Many developers publish skill repos. `gh` CLI is authenticated as `clawbotai`. 5,000 API requests/hour.
- **VoltAgent/awesome-openclaw-skills**: Curated awesome list (13.7K★). 2,999 skills after filtering 2,748 junk (spam, malicious, dupes).
- **396 skills identified as malicious** by security researchers. Security scanning is mandatory before installation.

**Existing tools we can leverage:**
- `clawhub search "<query>" --limit N` — Vector search across ClawHub registry
- `clawhub install <slug>` — Install a skill to `./skills/`
- `gh api search/repositories -f q="..." -f sort=stars -f per_page=N` — GitHub repo search
- `gh api repos/<owner>/<repo>/contents/<path>` — Read files from repos
- `gh api users/<username>` — Developer profile data
- `python3 skills/agent-guardrails/scripts/guardrails.py scan --path <file>` — Security scan for secrets, PII, prompt injection
- `bash skills/project-structure/scripts/validate-structure.sh <path> skill` — Structural validation

---

## Hard Constraints

1. **Python 3.9** — Use `typing.Optional[X]`, `typing.List[X]`, `typing.Dict[K,V]` — NOT `X | None`, `list[X]`, `dict[K,V]`
2. **Zero external dependencies** — stdlib only (json, sqlite3, subprocess, re, ast, os, sys, datetime, dataclasses, pathlib, urllib, math, hashlib, argparse, textwrap, logging). No pip installs.
3. **All CLI tools called via `subprocess.run()`** — Shell out to `clawhub`, `gh`, `python3` for external integrations
4. **SQLite for persistence** — Database at `memory/skill-scout/scout.db`. Use WAL mode. Create `memory/skill-scout/` directory if it doesn't exist.
5. **JSON reports** — All reports also written as JSON to `memory/skill-scout/` for agent consumption
6. **No network calls from Python** — Use `gh api` and `clawhub` CLI for all network access. Do not use `urllib.request` or `http.client` directly.
7. **Aggressive caching** — Never re-evaluate a skill that hasn't changed. Store content hashes. Re-evaluate monthly max.
8. **Every function must have a Google-style docstring** with Args/Returns sections
9. **Module-level docstrings** on every .py file
10. **argparse CLI** on every script with subcommands
11. **All output is JSON** (printed to stdout) for agent parsing. Use `json.dumps(result, indent=2)`
12. **Graceful degradation** — If `clawhub` is not installed or `gh` is not authenticated, skip that source and continue with available sources. Never crash on missing tools.

---

## Script 1: `scripts/discover.py` (~400 LOC)

### Purpose
Find skills and developers across ClawHub, GitHub, and awesome lists.

### CLI Interface
```bash
python3 scripts/discover.py clawhub --query "calendar" --limit 20
python3 scripts/discover.py github --query "openclaw skill" --limit 20
python3 scripts/discover.py awesome --refresh
python3 scripts/discover.py developer --username "steipete"
python3 scripts/discover.py sweep --categories "devops,security,memory,calendar,email"
```

### Subcommands

**`clawhub`** — Search ClawHub registry
- Run: `clawhub search "<query>" --limit N`
- Parse the CLI output (format: `<slug> v<version>  <name>  (<score>)`)
- Store results in `scout.db` → `skills` table
- Return: JSON array of skill records

**`github`** — Search GitHub for skill repositories
- Run: `gh api search/repositories -f q="<query>" -f sort=stars -f per_page=<limit>` with `--jq` for field extraction
- For each repo, check if it contains SKILL.md files: `gh api repos/<owner>/<repo>/git/trees/HEAD --jq '.tree[] | select(.path | test("SKILL.md"))'`
- Extract author username, stars, forks, description, last push date
- Store in `scout.db` → `skills` table with `source=github`
- Return: JSON array of skill records

**`awesome`** — Parse the VoltAgent awesome list
- Fetch: `gh api repos/VoltAgent/awesome-openclaw-skills/contents/README.md --jq .content` → base64 decode
- Parse markdown: Extract category headers (`### Category Name`) and skill entries (`- [name](url) - description`)
- Extract slug, GitHub URL, category, description from each entry
- Store in `scout.db` → `skills` table with `source=awesome-list`
- Cache with timestamp — only re-fetch if last fetch > 24h ago
- Return: JSON with categories and skill counts

**`developer`** — Build a developer profile
- Fetch: `gh api users/<username>` → followers, public_repos, created_at
- Fetch: `gh api users/<username>/repos --jq '.[].full_name' -f per_page=100 -f sort=stars`
- Cross-reference repos against known skill repos in `scout.db`
- Store in `scout.db` → `developers` table
- Return: JSON developer profile

**`sweep`** — Run discovery across multiple categories
- Takes comma-separated category list
- For each category: run clawhub search + github search
- Deduplicate by slug
- Return: JSON summary with total discovered per category

### Database Schema (create on first run)

```sql
CREATE TABLE IF NOT EXISTS skills (
    slug TEXT PRIMARY KEY,
    source TEXT NOT NULL,           -- 'clawhub', 'github', 'awesome-list'
    source_url TEXT,
    author TEXT,
    version TEXT,
    description TEXT,
    category TEXT,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    last_updated TEXT,              -- ISO 8601
    content_hash TEXT,              -- SHA256 of SKILL.md content for change detection
    first_seen TEXT NOT NULL,       -- ISO 8601
    last_evaluated TEXT,            -- ISO 8601, NULL if never evaluated
    quality_score REAL,             -- NULL if not evaluated
    quality_tier TEXT,              -- S/A/B/C/F
    installed INTEGER DEFAULT 0,   -- boolean
    flagged INTEGER DEFAULT 0,     -- security concern
    raw_data TEXT                   -- JSON blob for source-specific extras
);

CREATE TABLE IF NOT EXISTS developers (
    username TEXT PRIMARY KEY,
    github_url TEXT,
    tier TEXT,                      -- Master/Expert/Contributor/Watched
    score REAL,
    skill_count INTEGER DEFAULT 0,
    avg_skill_quality REAL,
    best_skill TEXT,
    followers INTEGER DEFAULT 0,
    total_stars INTEGER DEFAULT 0,
    account_age_days INTEGER,
    last_activity TEXT,             -- ISO 8601
    watched INTEGER DEFAULT 0,     -- boolean
    first_seen TEXT NOT NULL,
    last_evaluated TEXT,
    raw_data TEXT                   -- JSON blob
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,     -- ISO 8601
    overall_score REAL NOT NULL,
    tier TEXT NOT NULL,
    dimension_scores TEXT NOT NULL, -- JSON: {"documentation": 22, ...}
    security_flags TEXT,            -- JSON array of concerns found
    notes TEXT,
    FOREIGN KEY (slug) REFERENCES skills(slug)
);

CREATE TABLE IF NOT EXISTS watch_list (
    username TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    reason TEXT,
    last_checked TEXT,
    FOREIGN KEY (username) REFERENCES developers(username)
);
```

---

## Script 2: `scripts/evaluate.py` (~500 LOC)

### Purpose
Score a skill's quality across 7 dimensions. Can evaluate from local path OR by fetching from GitHub/ClawHub.

### CLI Interface
```bash
python3 scripts/evaluate.py score --slug "agent-memory"                    # Evaluate by slug (fetches from source)
python3 scripts/evaluate.py score --path /path/to/skill/                   # Evaluate local skill directory
python3 scripts/evaluate.py batch --slugs "slug1,slug2,slug3"              # Batch evaluate
python3 scripts/evaluate.py security --path /path/to/skill/                # Security-only deep scan
python3 scripts/evaluate.py compare --slug "their-skill" --ours "our-skill" # Head-to-head comparison
```

### Scoring Dimensions (100-point scale)

**1. Documentation Quality (25 points max)**
- Has SKILL.md: +8 (required — if missing, entire skill scores 0)
- SKILL.md > 100 lines with real content (not boilerplate): +4
- Has README.md: +4
- Has CHANGELOG.md: +3
- Has inline comments in scripts (>10% comment-to-code ratio): +3
- No `[TODO]`, `[PLACEHOLDER]`, `lorem ipsum` detected: +3

**2. Code Quality (20 points max)**
- Has `scripts/` directory with actual code: +5
- Python files have type hints (check for `: str`, `: int`, `-> `, `Optional`, `List`, `Dict`): +4
- Functions have docstrings (>60% of functions): +4
- Has error handling (try/except blocks): +3
- No hardcoded file paths outside workspace: +2
- PEP 8 basics (no tabs, lines < 120 chars, snake_case functions): +2

**3. Community Signal (15 points max)**
- GitHub stars: 0=0, 1-10=3, 11-50=6, 51-200=9, 200+=12
- Forks > 0: +3

**4. Security Posture (15 points max)** — Start at 15, subtract for violations
- Contains `eval()` or `exec()` with non-literal args: -5
- Contains `os.system()` or `subprocess` with `shell=True` and string interpolation: -5
- Contains hardcoded API keys/tokens (regex: `[A-Za-z0-9]{32,}` near `key`, `token`, `secret`): -5
- Contains `pickle.loads` from untrusted source: -3
- Accesses keychain/credentials outside documented scope: -5
- Makes network calls to non-standard domains: -3
- Attempts to modify files outside its own directory: -3
- If score goes below 0, set to 0 and flag the skill

**5. Maintenance Health (10 points max)**
- Last commit within 30 days: +4; within 90 days: +2; older: 0
- Has >5 commits total: +3
- Has >1 version published: +3

**6. Structural Compliance (10 points max)**
- Has `_meta.json`: +4
- `_meta.json` has `slug`, `version`, `description` fields: +3
- Has `CONTRIBUTING.md`: +3

**7. Compatibility (5 points max)**
- No dependencies beyond Python stdlib: +3
- Specifies Python 3.9+ compatible syntax: +2

### Implementation Notes

**For remote evaluation (by slug):**
1. Look up slug in `scout.db` to get `source_url`
2. If GitHub source: fetch file list via `gh api repos/<owner>/<repo>/git/trees/HEAD?recursive=1`
3. Fetch key files: SKILL.md, README.md, _meta.json, CHANGELOG.md, CONTRIBUTING.md, and up to 5 script files
4. Use `gh api repos/<owner>/<repo>/contents/<path> --jq .content` → base64 decode
5. Run all scoring dimensions on fetched content
6. Store evaluation in `evaluations` table

**For local evaluation (by path):**
1. Read files directly from disk
2. For security scan, also call: `python3 skills/agent-guardrails/scripts/guardrails.py scan --path <file>` on each script
3. Run validate-structure.sh: `bash skills/project-structure/scripts/validate-structure.sh <path> skill`

**Security scanning (the `security` subcommand):**
Use Python's `ast` module for reliable detection:
```python
import ast
tree = ast.parse(source_code)
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        # Check for eval(), exec(), os.system(), subprocess with shell=True
        # Check for open() on paths outside the skill directory
        # Check for import of network libraries (requests, urllib, http.client, socket)
```
Also use regex for credential patterns:
```python
CREDENTIAL_PATTERNS = [
    r'(?i)(api[_-]?key|secret|token|password)\s*[=:]\s*["\'][A-Za-z0-9+/=]{16,}',
    r'AKIA[0-9A-Z]{16}',           # AWS access key
    r'sk-[a-zA-Z0-9]{20,}',        # OpenAI key
    r'ghp_[a-zA-Z0-9]{36}',        # GitHub PAT
]
```

**The `compare` subcommand:**
- Evaluate both skills
- Output side-by-side dimension scores
- Declare winner per dimension + overall
- Recommend: keep ours, replace with theirs, or merge capabilities

---

## Script 3: `scripts/scout.py` (~500 LOC)

### Purpose
Unified CLI for ranking, acquisition, gap analysis, reporting, and watch list management. This is the "brain" that ties discovery and evaluation together.

### CLI Interface
```bash
# Developer ranking
python3 scripts/scout.py rank-developers --min-skills 2 --limit 20
python3 scripts/scout.py rank-skills --category "devops" --limit 20 --min-score 60

# Gap analysis
python3 scripts/scout.py gaps --our-skills /path/to/skills/  # defaults to ../../ relative to script
python3 scripts/scout.py recommend --category "calendar" --limit 5

# Acquisition
python3 scripts/scout.py acquire --slug "their-skill" --dry-run
python3 scripts/scout.py acquire --slug "their-skill" --install

# Watch list
python3 scripts/scout.py watch --add "username" --reason "Top devops developer"
python3 scripts/scout.py watch --check                        # Check all watched devs for new activity
python3 scripts/scout.py watch --list

# Reporting
python3 scripts/scout.py report --type ecosystem              # Full ecosystem overview
python3 scripts/scout.py report --type developers              # Developer hierarchy
python3 scripts/scout.py report --type gaps                    # Gap analysis
python3 scripts/scout.py report --type alerts                  # New skills from watched developers

# Database
python3 scripts/scout.py stats                                 # DB statistics
python3 scripts/scout.py prune --days 90                       # Remove stale records
```

### Subcommand Details

**`rank-developers`**
- Query all developers from `scout.db`
- Calculate developer score:
  - 40%: Average quality score of their skills
  - 15%: log2(1 + skill_count) / log2(1 + 20) × 100 (log-scaled, caps at 20 skills)
  - 15%: GitHub reputation = min(100, (followers/100 + total_stars/1000 + account_age_days/365) × 10)
  - 15%: Consistency = max(0, 100 - std_dev_of_skill_scores × 2)
  - 15%: Freshness = days_since_last_activity → 0-7 days: 100, 8-30: 75, 31-90: 50, 91-180: 25, 180+: 0
- Assign tier: Master (≥5 skills, avg ≥85, active 30d), Expert (≥3, avg ≥70, active 90d), Contributor (≥1, avg ≥60), Watched (else)
- Output: Ranked JSON list with tier, score, breakdown

**`rank-skills`**
- Query skills with optional category and min-score filter
- Sort by quality_score DESC
- Output: Ranked JSON list with tier badges

**`gaps`**
- Scan our skills directory: read each `_meta.json` → extract slug, description, tags
- Build a capability map of what we cover
- Query `scout.db` for high-scoring external skills (≥75) we DON'T have
- Group by category
- Output: JSON with `{"covered": [...], "gaps": [{"category": "...", "recommended_skills": [...]}]}`

**`recommend`**
- For a given category, find the top N skills by quality score
- Exclude skills we already have (check `installed` flag or match slugs against our skills directory)
- Output: JSON with skill details + quality breakdown + installation command

**`acquire`**
- `--dry-run`: Evaluate the skill, run security scan, report findings without installing
- `--install`: After passing all checks:
  1. Evaluate quality (must be ≥60)
  2. Run security scan (must be clean — 0 critical flags)
  3. Run `clawhub install <slug>` (or `gh` clone if not on ClawHub)
  4. Run `validate-structure.sh` on installed skill
  5. Update `scout.db` → set `installed=1`
  6. Output: JSON with install status, score, any warnings
- If security scan finds issues, output them and refuse to install. The agent must present these to the user.

**`watch`**
- `--add`: Add developer to watch list with reason
- `--check`: For each watched developer, fetch their latest repos via GitHub API. Compare against last_checked. If new skill repos found since last check, auto-evaluate them and add to alerts.
- `--list`: Show all watched developers with their tier and last check date

**`report`**
- Generates JSON reports saved to `memory/skill-scout/`:
  - `ecosystem-report.json`: Total skills by source, tier distribution, top 20 skills, top 10 developers
  - `developer-hierarchy.json`: All ranked developers with tiers
  - `gap-analysis.json`: Our coverage vs ecosystem, recommended acquisitions
  - `watch-alerts.json`: New skills from watched developers since last check

**`stats`**
- Total skills in DB, by source, by tier
- Total developers, by tier
- Total evaluations
- Last sweep date
- DB file size

**`prune`**
- Delete skills not seen in N days (default 90)
- Delete evaluations older than N days
- VACUUM the database

---

## `_meta.json`

```json
{
  "slug": "skill-scout",
  "name": "Skill Scout",
  "version": "1.0.0",
  "description": "Autonomous skill intelligence — discover, evaluate, rank, and acquire high-quality OpenClaw skills from the ecosystem. Monitors ClawHub, GitHub, and awesome lists to find battle-tested skills instead of building from scratch.",
  "author": "clawbotai",
  "license": "MIT",
  "tags": ["meta", "discovery", "quality", "ecosystem", "automation"],
  "permissions": {
    "filesystem": ["read", "write"],
    "execution": ["shell"]
  },
  "requires": {
    "tools": ["clawhub", "gh"],
    "python": ">=3.9"
  }
}
```

---

## `SKILL.md` — Agent Instruction Manual

Write this as a practical playbook for an LLM agent. NOT a reference manual. Structure:

1. **What This Does** (2-3 sentences)
2. **Quick Commands** — The 10 most useful commands with copy-paste examples
3. **Workflow: First Run** — How to bootstrap the database with initial discovery
4. **Workflow: Finding Skills** — How to search for specific capabilities
5. **Workflow: Evaluating Quality** — How to score and compare skills
6. **Workflow: Acquiring a Skill** — The full security-checked installation flow
7. **Workflow: Monitoring the Ecosystem** — Setting up developer watch lists and sweeps
8. **Decision Framework: Build vs Acquire** — When to build a skill from scratch vs finding one
   - Acquisition: <500 tokens to evaluate, instant install
   - Building: 50-200K tokens, hours of work
   - Rule: Always search first. Build only if nothing scores ≥75 in the relevant category.
9. **Quality Tiers Explained** — S/A/B/C/F with what each means in practice
10. **Developer Tiers Explained** — Master/Expert/Contributor/Watched
11. **Security Rules** — Never install without security scan. Never auto-install flagged skills. Always present security findings to user.
12. **Anti-Patterns** — Don't evaluate every skill on ClawHub (5,705!). Don't trust star counts alone. Don't install skills with `eval()`. Don't skip the security scan "just this once".

---

## `README.md`

Human-readable installation and usage guide. Include:
- What the skill does (paragraph)
- Architecture diagram (ASCII)
- Quick start (3 commands to get going)
- All CLI commands with examples
- Database location and schema overview
- Security model
- Rate limit awareness (GitHub 5K/hr, ClawHub unknown)

---

## `CHANGELOG.md`

Keep a Changelog format. Version 1.0.0, date 2026-02-11. List all features built.

---

## `CONTRIBUTING.md`

- Python 3.9, stdlib only, Google-style docstrings
- How to add new scoring dimensions
- How to add new discovery sources
- Testing approach (manual CLI commands)
- PR process

---

## Quality Gates (verify before declaring done)

1. All 3 Python scripts run without errors: `python3 scripts/discover.py --help`, `python3 scripts/evaluate.py --help`, `python3 scripts/scout.py --help`
2. Database creates cleanly on first run
3. `clawhub search "calendar" --limit 5` integration works (parses output correctly)
4. `gh api search/repositories` integration works (parses JSON correctly)
5. Security scan uses `ast` module, not just regex
6. All functions have Google-style docstrings
7. No `X | None` syntax anywhere (Python 3.9)
8. Total file size < 60KB
9. Passes: `bash skills/project-structure/scripts/validate-structure.sh skills/skill-scout skill` with 0 errors

---

## Design Decisions (already made — follow these)

1. **Always require user approval for installation** — even S-tier skills from Master developers. Security first.
2. **Use AST parsing for security scan** — `ast.walk()` is reliable and available in stdlib. Supplement with regex for credential patterns.
3. **Track skill lineage** — Store `content_hash` (SHA256 of SKILL.md) to detect forks/copies. Flag duplicates.
4. **Use CLI wrappers, not direct API** — `clawhub` and `gh` handle auth, rate limiting, and pagination. Don't reinvent.
5. **Log-scale skill count in developer scoring** — Prevents gaming by publishing 50 low-quality skills.
6. **Monthly re-evaluation cycle** — Don't re-score skills that haven't changed (check `content_hash`).
7. **Graceful degradation** — If ClawHub CLI missing, use GitHub only. If GitHub not authenticated, use ClawHub only. If neither, fail with clear error.
