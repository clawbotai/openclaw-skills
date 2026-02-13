---
name: skill-scout
description: Autonomous skill discovery and evaluation — search ClawHub and GitHub, score quality across 7 dimensions, quarantine workflow, security gates, and developer ranking.
---

# skill-scout — Autonomous Skill Intelligence

Find battle-tested skills instead of building from scratch. Discover across ClawHub (5,700+ skills) and GitHub, score quality across 7 dimensions, rank developers, and acquire with security gates. Saves 100-400× tokens per successful acquisition.

**All scripts live in:** `skills/skill-scout/scripts/`

---

## Quick Commands

```bash
# Search ClawHub
python3 scripts/discover.py clawhub --query "calendar" --limit 10

# Search GitHub
python3 scripts/discover.py github --query "openclaw email skill" --limit 10

# Evaluate a local skill
python3 scripts/evaluate.py score --path /path/to/skill/

# Evaluate a remote skill by slug
python3 scripts/evaluate.py score --slug "calendar"

# Security scan only
python3 scripts/evaluate.py security --path /path/to/skill/

# Compare two skills head-to-head
python3 scripts/evaluate.py compare --slug "their-calendar" --ours "skills/calendar"

# Rank top developers
python3 scripts/scout.py rank-developers --min-skills 2 --limit 20

# Find gaps in our skillset
python3 scripts/scout.py gaps

# Acquire a skill (dry run first)
python3 scripts/scout.py acquire --slug "calendar" --dry-run

# Database stats
python3 scripts/scout.py stats
```

---

## Workflow: First Run

Bootstrap the database with an initial discovery sweep:

```bash
# 1. Sweep key categories
python3 scripts/discover.py sweep --categories "calendar,email,devops,security,memory,browser,automation,search"

# 2. Parse the curated awesome list (2,999 skills)
python3 scripts/discover.py awesome --refresh

# 3. Check stats
python3 scripts/scout.py stats
```

---

## Workflow: Finding a Skill

When the user needs a capability you don't have:

1. **Search ClawHub** (vector search, fast):
   ```bash
   python3 scripts/discover.py clawhub --query "what user needs" --limit 10
   ```

2. **Search GitHub** (broader, catches non-ClawHub repos):
   ```bash
   python3 scripts/discover.py github --query "openclaw <capability>" --limit 10
   ```

3. **Evaluate top candidates**:
   ```bash
   python3 scripts/evaluate.py score --slug "best-result"
   ```

4. **Compare against our version** (if we have one):
   ```bash
   python3 scripts/evaluate.py compare --slug "theirs" --ours "skills/ours"
   ```

---

## Workflow: Evaluating Quality

The scoring engine rates skills on a 100-point scale across 7 dimensions:

| Dimension | Max | What It Checks |
|-----------|-----|----------------|
| Documentation | 25 | SKILL.md, README, CHANGELOG, comments, no placeholders |
| Code Quality | 20 | Type hints, docstrings, error handling, PEP 8 |
| Community | 15 | Stars, forks |
| Security | 15 | AST: eval/exec/os.system/shell=True. Regex: API keys, secrets |
| Maintenance | 10 | Recency, version count, download activity |
| Structure | 10 | _meta.json, required fields, CONTRIBUTING.md |
| Compatibility | 5 | Stdlib-only, Python 3.9 syntax |

**Quality Tiers:**
- **S (≥90):** Elite — auto-recommend
- **A (75-89):** High quality — recommend with summary
- **B (60-74):** Acceptable — list with caveats
- **C (40-59):** Low quality — monitor only
- **F (<40):** Poor/suspicious — exclude

**Critical security flags cap the tier at C** regardless of other scores.

---

## Workflow: Acquiring a Skill

**ALWAYS dry-run first. ALWAYS present security findings to the user.**

```bash
# Step 1: Dry run — evaluate + security scan
python3 scripts/scout.py acquire --slug "cool-skill" --dry-run

# Step 2: Review the output, especially security_flags
# Step 3: If clean and user approves:
python3 scripts/scout.py acquire --slug "cool-skill" --install
```

**Gates that must pass:**
1. Quality score ≥ 60
2. Zero critical security flags
3. User approval (you present the findings, they decide)

**Never auto-install.** Even S-tier skills from Master developers need user sign-off.

---

## Workflow: Monitoring the Ecosystem

```bash
# Watch a prolific developer
python3 scripts/scout.py watch --add "steipete" --reason "Prolific skill author"

# Check watched developers for new activity
python3 scripts/scout.py watch --check

# Generate full ecosystem report
python3 scripts/scout.py report --type ecosystem

# Generate gap analysis
python3 scripts/scout.py report --type gaps
```

---

## Decision Framework: Build vs Acquire

```
Need a new capability?
  → Search ClawHub + GitHub first (costs ~500 tokens)
  → Found a skill scoring ≥75?
    YES → Acquire it (instant, near-free)
    NO  → Found ≥60?
      YES → Evaluate if it's worth adapting
      NO  → Build from scratch (50-200K tokens)
```

**Rule:** Always search first. Building is the last resort.

---

## Developer Tiers

| Tier | Criteria | Trust Level |
|------|----------|-------------|
| 🏆 Master | 5+ skills, avg ≥85, active 30d | High — review lightly |
| ⭐ Expert | 3+ skills, avg ≥70, active 90d | Medium — review normally |
| ✅ Contributor | 1+ skills, avg ≥60 | Standard — review carefully |
| 👀 Watched | New or unproven | Low — full review required |

---

## Security Rules

1. **Never install without running the security scan**
2. **Never auto-install flagged skills** — present flags to user
3. **Quarantine first:** Skills download to `_quarantine/`, get evaluated there, and only move to `skills/` after passing all gates
4. **AST analysis** catches: eval(), exec(), os.system(), subprocess(shell=True), pickle.loads(), network library imports
5. **AST evasion detection** catches: `__import__()`, `importlib.import_module()`, `getattr(os, ...)`, `compile()` with dynamic args
6. **Markdown security scanner** catches: `curl|sh`, `wget`, `chmod +x`, `base64 -d`, inline Python exec, global npm/pip installs, raw IP URLs, URL shorteners, paste service links, obfuscated payloads
7. **Regex detection** catches: AWS keys, OpenAI keys, GitHub PATs, hardcoded passwords, private keys
8. **Critical flags block installation** — no exceptions
9. **Tier cap:** Any skill with critical flags is capped at tier C

---

## Anti-Patterns

- ❌ Don't evaluate every skill on ClawHub (5,700+ is too many). Search targeted.
- ❌ Don't trust star counts alone — a skill with 1000 stars and eval() is still dangerous.
- ❌ Don't install skills with `eval()` or `shell=True` — ever.
- ❌ Don't skip the security scan "just this once."
- ❌ Don't over-parallelize sweeps — 5 categories at a time is the sweet spot.
- ❌ Don't re-evaluate unchanged skills — check content_hash first.
