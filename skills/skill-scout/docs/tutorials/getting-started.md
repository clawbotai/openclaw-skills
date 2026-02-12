# Getting Started with skill-scout

## Prerequisites

- Python 3.9+ (pre-installed on macOS)
- `clawhub` CLI (optional): `npm i -g clawhub`
- `gh` CLI (optional): `brew install gh && gh auth login`

skill-scout degrades gracefully — if either CLI is missing, it uses the other.

## Step 1: Bootstrap the Database

Run a discovery sweep across key categories to seed the database:

```bash
cd /Users/clawai/openclaw/workspace/skills/skill-scout/scripts

python3 discover.py sweep --categories "calendar,email,devops,security,memory,browser"
```

This searches both ClawHub and GitHub in parallel (5 workers), storing results in `memory/skill-scout/scout.db`.

## Step 2: Import the Curated Awesome List

The VoltAgent awesome list has 2,999 pre-filtered skills (spam, malicious, and dupes removed):

```bash
python3 discover.py awesome --refresh
```

Results are cached for 24 hours to avoid redundant API calls.

## Step 3: Check What You Found

```bash
python3 scout.py stats
```

Output (JSON):
```json
{
  "total_skills": 42,
  "total_developers": 0,
  "total_evaluations": 0,
  "skills_by_source": {"clawhub": 18, "github": 12, "awesome-list": 12},
  "db_size_bytes": 45056
}
```

## Step 4: Evaluate a Skill

Score a skill from ClawHub:

```bash
python3 evaluate.py score --slug "calendar"
```

Or evaluate one of your own local skills:

```bash
python3 evaluate.py score --path ../../agent-guardrails
```

The output includes a 100-point score with per-dimension breakdown and any security flags.

## Step 5: Find Gaps in Your Skillset

```bash
python3 scout.py gaps
```

This compares your installed skills against the ecosystem and recommends high-scoring skills you don't have.

## Step 6: Acquire a Skill (With Security Gates)

Always dry-run first:

```bash
python3 scout.py acquire --slug "calendar" --dry-run
```

Review the output — especially `security_flags`. If clean and you approve:

```bash
python3 scout.py acquire --slug "calendar" --install
```

The acquisition pipeline enforces: quality ≥ 60, zero critical security flags, and user approval.

## What's Next

- **Watch developers**: `python3 scout.py watch --add "prolific-dev" --reason "Great skills"`
- **Generate reports**: `python3 scout.py report --type ecosystem`
- **Compare skills**: `python3 evaluate.py compare --slug "their-skill" --ours "our-skill"`
- **Prune stale data**: `python3 scout.py prune --days 90`
