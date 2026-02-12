# Prompt: Design the `skill-scout` Skill — Autonomous Skill Intelligence & Acquisition

## Concept

An autonomous intelligence-gathering skill that continuously discovers, evaluates, ranks, and optionally acquires high-quality OpenClaw skills from the ecosystem. It monitors GitHub repositories, the ClawHub registry (5,705+ published skills), and individual developer activity to build a ranked hierarchy of developers and skills — then recommends or auto-installs the best ones.

**The value proposition:** Instead of spending 200K+ tokens building a skill from scratch, find a battle-tested one that already exists, evaluate its quality, and install it in seconds. This skill pays for itself in one acquisition.

---

## Ecosystem Intelligence (What We Learned)

### Data Sources Available

| Source | Access Method | Data Available |
|--------|-------------|----------------|
| **ClawHub Registry** | `clawhub search <query>` (CLI, installed at `/opt/homebrew/bin/clawhub` v0.5.0) | 5,705 skills, vector search, stars, downloads, versions |
| **GitHub API** | `gh api` (CLI, authenticated as `clawbotai`) | Repos, stars, forks, contributors, commit history, file contents |
| **GitHub Search** | `gh api search/repositories` | Find skill repos by topic/description, sort by stars |
| **Awesome Lists** | VoltAgent/awesome-openclaw-skills (13.7K★, 2,999 curated skills), sundial-org/awesome-openclaw-skills | Pre-filtered, categorized |
| **ClawHub Web** | clawhub.ai | Browsable catalog, VirusTotal integration |

### Key Ecosystem Facts

- **5,705 skills** on ClawHub as of Feb 2026
- **2,748 filtered out** by VoltAgent's awesome list (1,180 spam, 672 crypto, 492 dupes, 396 malicious)
- **2,999 curated skills** remain after filtering
- Skills follow the AgentSkill convention: SKILL.md + supporting files
- `clawhub install <slug>` installs to `./skills/`
- `clawhub search` uses embedding-based vector search (not just keywords)
- GitHub repos often contain multiple skills in one repo
- Major skill repos: openclaw/skills (official), BankrBot/openclaw-skills, individual developer repos

---

## Architecture: What To Build

### Module 1: Discovery Engine

**Purpose:** Find skills and developers across the ecosystem.

**Data collection pipelines:**

1. **ClawHub Search Pipeline**
   - Input: Category keywords, capability gaps from our skillset
   - Method: `clawhub search "<query>" --limit N`
   - Output: Skill slugs with version, description, similarity score
   - Frequency: On-demand + weekly sweep of key categories

2. **GitHub Repository Scanner**
   - Input: Search queries targeting skill repos
   - Method: `gh api search/repositories` with queries like `"openclaw skill"`, `"agentskill SKILL.md"`, topic filters
   - Output: Repos with stars, forks, last commit, contributor list
   - Parse: Walk repo tree to find SKILL.md files → extract individual skills

3. **Awesome List Ingestion**
   - Input: VoltAgent/awesome-openclaw-skills README
   - Method: `gh api repos/VoltAgent/awesome-openclaw-skills/contents/README.md` → parse markdown links
   - Output: Categorized skill inventory with GitHub links

4. **Developer Profile Builder**
   - Input: GitHub usernames from discovered skills
   - Method: `gh api users/<username>`, `gh api users/<username>/repos`
   - Output: Developer profile (repos, followers, contribution history, skill count)

### Module 2: Quality Scoring Engine

**Purpose:** Apply our master-docs scoring methodology + additional quality signals to rank skills.

**Scoring Dimensions (100-point scale):**

| Dimension | Weight | Source | Metrics |
|-----------|--------|--------|---------|
| **Documentation Quality** | 25% | master-docs score-docs.sh methodology | Has SKILL.md (req), README, CHANGELOG, inline comments, no [TODO] placeholders |
| **Code Quality** | 20% | Static analysis | Has scripts/, type hints, error handling, docstrings, PEP 8, no hardcoded secrets |
| **Community Signal** | 15% | GitHub + ClawHub | Stars, forks, downloads, recent activity (last commit < 90 days) |
| **Security Posture** | 15% | Pattern scan | No eval(), no os.system() with string concat, no hardcoded credentials, no suspicious network calls, VirusTotal status |
| **Maintenance Health** | 10% | Git history | Commit frequency, issue response time, version count, changelog exists |
| **Structural Compliance** | 10% | validate-structure.sh methodology | Has _meta.json with required fields, proper directory layout |
| **Compatibility** | 5% | Metadata inspection | Python version compat, dependency count, platform tags |

**Quality Tiers:**

| Tier | Score | Label | Action |
|------|-------|-------|--------|
| S | ≥90 | Elite | Auto-recommend for installation |
| A | 75–89 | High Quality | Recommend with summary |
| B | 60–74 | Acceptable | List with caveats |
| C | 40–59 | Low Quality | Monitor only |
| F | <40 | Poor/Suspicious | Exclude |

### Module 3: Developer Ranking System

**Purpose:** Build a hierarchy of the best skill developers in the ecosystem.

**Developer Score = Weighted average of their skills' scores + activity signals**

**Metrics:**

| Signal | Weight | Description |
|--------|--------|-------------|
| **Avg Skill Quality** | 40% | Mean quality score across all their skills |
| **Skill Count** | 15% | Number of published skills (log-scaled to prevent gaming) |
| **GitHub Reputation** | 15% | Followers, total stars across repos, account age |
| **Consistency** | 15% | Std deviation of skill scores (low = consistent quality) |
| **Freshness** | 15% | Recency of last publish/commit |

**Developer Tiers:**

| Tier | Description |
|------|-------------|
| **🏆 Master** | 5+ skills, avg score ≥85, active in last 30 days |
| **⭐ Expert** | 3+ skills, avg score ≥70, active in last 90 days |
| **✅ Contributor** | 1+ skills, avg score ≥60 |
| **👀 Watched** | New or unproven, monitoring |

**Developer Watch List:** Track top developers via cron — when they publish new skills, auto-evaluate and alert.

### Module 4: Gap Analysis & Acquisition

**Purpose:** Compare our skillset against the ecosystem and recommend acquisitions.

**Gap detection:**
1. Catalog our 34 skills by capability tags
2. Map ClawHub categories to our capabilities
3. Identify categories where we have 0 coverage but high community activity
4. Find skills that complement our existing ones (e.g., a better calendar skill)

**Acquisition workflow:**
1. Identify gap or highly-rated skill
2. Run full quality scoring
3. Run security scan (guardrails scan on SKILL.md + all scripts)
4. If score ≥75 and security clean → recommend to user
5. If user approves → `clawhub install <slug>` or manual git clone
6. Run validate-structure.sh on installed skill
7. If validation passes → add to inventory

**Deduplication:** Before recommending, check if we already have a skill covering the same capability. If our version scores higher, skip. If theirs is better, flag for potential replacement.

### Module 5: Monitoring & Reporting

**Purpose:** Continuous intelligence feed.

**Scheduled tasks (via cron or heartbeat):**

| Task | Frequency | Description |
|------|-----------|-------------|
| Category sweep | Weekly | Search ClawHub for top skills in each category |
| Developer watch | Weekly | Check watched developers for new publications |
| Trending scan | Daily | GitHub trending repos with "openclaw" topic |
| Gap report | Monthly | Full comparison of our skills vs ecosystem |
| Security re-scan | Monthly | Re-evaluate installed external skills |

**Reports generated:**
- `memory/skill-scout/ecosystem-report.json` — Full ranked inventory
- `memory/skill-scout/developer-hierarchy.json` — Ranked developer list
- `memory/skill-scout/gap-analysis.json` — Missing capabilities
- `memory/skill-scout/watch-alerts.json` — New skills from watched developers

---

## Data Model

### Skill Record
```json
{
  "slug": "agent-memory",
  "source": "clawhub|github|awesome-list",
  "source_url": "https://github.com/...",
  "author": "username",
  "version": "1.2.0",
  "description": "...",
  "category": "agent-infrastructure",
  "quality_score": 87,
  "quality_tier": "A",
  "dimension_scores": {
    "documentation": 22,
    "code_quality": 18,
    "community": 12,
    "security": 14,
    "maintenance": 8,
    "structure": 9,
    "compatibility": 4
  },
  "stars": 142,
  "downloads": 3200,
  "last_updated": "2026-02-01",
  "installed": false,
  "replaces": null,
  "first_seen": "2026-02-11",
  "last_evaluated": "2026-02-11"
}
```

### Developer Record
```json
{
  "username": "steipete",
  "github_url": "https://github.com/steipete",
  "tier": "Master",
  "score": 92,
  "skill_count": 8,
  "avg_skill_quality": 88,
  "best_skill": "agent-memory",
  "followers": 5200,
  "total_stars": 45000,
  "account_age_days": 4380,
  "last_activity": "2026-02-10",
  "watched": true,
  "skills": ["slug1", "slug2", "..."]
}
```

---

## Implementation Considerations

### Rate Limits
- **GitHub API:** 5,000 requests/hour (authenticated via `gh`)
- **ClawHub CLI:** Unknown limits — assume reasonable (10 req/sec)
- **Brave Search:** 1 req/sec, 2,000/month (use sparingly, prefer API access)
- **Strategy:** Cache aggressively. Score once, re-evaluate monthly. Don't re-scan unchanged repos.

### Security Concerns
- **Malicious skills:** VoltAgent found 396 malicious skills. We MUST scan before installing.
- **Supply chain risk:** A skill's scripts run with full filesystem/exec access. Treat external skills like untrusted code.
- **Scanning pipeline:** Before any installation:
  1. `guardrails.py scan` on all text files in the skill
  2. Check for `eval()`, `exec()`, `os.system()`, `subprocess` with shell=True
  3. Check for network calls to unexpected domains
  4. Check for attempts to read credentials/keychain
  5. Check VirusTotal status on ClawHub if available

### Storage
- SQLite database at `memory/skill-scout/scout.db`
- Tables: `skills`, `developers`, `evaluations`, `watch_list`, `scan_results`
- JSON reports for agent-readable summaries

### Cost Optimization
- This skill EXISTS to save tokens. A typical skill costs 50-200K tokens to build.
- Finding a high-quality existing skill costs ~500 tokens (search + evaluate).
- ROI: 100x-400x token savings per successful acquisition.
- Monthly sweep of ~100 skills costs ~5K tokens total.

---

## Scripts to Build

| File | Purpose | LOC Est |
|------|---------|---------|
| `scripts/discover.py` | Discovery engine: ClawHub search, GitHub scan, awesome list parsing | ~400 |
| `scripts/evaluate.py` | Quality scoring engine: doc quality, code quality, security, community signals | ~500 |
| `scripts/rank.py` | Developer ranking + skill hierarchy + tier assignment | ~200 |
| `scripts/acquire.py` | Gap analysis, security scan, installation workflow | ~300 |
| `scripts/report.py` | Generate reports, watch alerts, ecosystem stats | ~200 |
| `SKILL.md` | Agent instruction manual | ~300 lines |

**Total estimated:** ~1,900 LOC Python + 300 lines SKILL.md

---

## Open Questions for Analysis

1. **Should acquisitions be auto-installed or always require user approval?** Given security concerns, probably always approve. But for S-tier skills from Master developers, maybe auto-install with notification?

2. **How deep should code analysis go?** Full AST parsing (ast module) vs regex pattern matching? AST is more reliable but heavier. Regex catches obvious issues fast.

3. **Should we track skill lineage?** Many skills are forks/copies. Identifying the "canonical" version vs copies would improve recommendations.

4. **ClawHub API vs CLI?** The CLI works but is slower than direct API calls. Should we discover the API endpoints and call them directly?

5. **Integration with skill-evolutionary-loop?** When a gap is identified, should we: (a) find an external skill, (b) build one via the evolutionary loop, or (c) evaluate both options and pick the cheaper/better one?

6. **Competitive intelligence?** Should we monitor what OTHER OpenClaw users are building and installing (public data only)? GitHub activity is public — we could track which skills are gaining traction fastest.

---

## Research References

- VoltAgent/awesome-openclaw-skills: 2,999 curated skills, filtering methodology (spam/malicious/dupe removal)
- ClawHub docs: Vector search, versioning, moderation, CLI commands
- openclaw/clawhub source: Registry architecture, API design
- Our master-docs score-docs.sh: Documentation quality scoring (adapting for external skills)
- Our agent-guardrails: Security scanning pipeline for untrusted code
- arXiv 2510.25445: Multi-agent orchestration for parallel evaluation
