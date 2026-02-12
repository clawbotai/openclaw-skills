# Changelog

All notable changes to skill-scout will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-02-11

### Added

#### Discovery Engine (discover.py)
- ClawHub search with real CLI output parsing (text format, not JSON)
- ClawHub inspect integration for rich metadata (stars, downloads, author)
- GitHub repository search via `gh api search/repositories`
- GitHub raw file fetching via `gh api repos/.../contents/...`
- VoltAgent awesome-openclaw-skills README parser (regex-based, 2,999 skills)
- Developer profile builder from GitHub API data
- Multi-category parallel sweep with ThreadPoolExecutor (5 workers)
- Circuit breaker pattern: 3 consecutive failures → cached DB fallback
- 24-hour cache for awesome list to avoid redundant API calls

#### Quality Scoring Engine (evaluate.py)
- 7-dimension scoring (100-point scale): documentation, code quality, community, security, maintenance, structure, compatibility
- AST-based security analysis: eval(), exec(), os.system(), subprocess(shell=True), pickle.loads(), network library imports
- Async function (AsyncFunctionDef) support in AST analysis
- Regex credential detection: AWS keys, OpenAI keys, GitHub PATs, GitLab PATs, hardcoded passwords, private keys
- Code metrics via AST: function count, docstring coverage, type hint coverage, exception handling
- Python 3.9 stdlib module whitelist for compatibility checking
- Critical security flags cap tier at C regardless of other scores
- Local path evaluation (read files from disk)
- Remote evaluation (fetch files via clawhub inspect or gh API)
- Head-to-head skill comparison with per-dimension breakdown
- Batch evaluation for multiple slugs
- Content hashing (SHA-256) for change detection

#### Orchestrator (scout.py)
- Developer ranking: weighted composite (quality 40%, volume 15%, reputation 15%, consistency 15%, freshness 15%)
- Developer tiers: Master / Expert / Contributor / Watched
- Skill ranking with category and score filters
- Gap analysis: compares our skills vs ecosystem, finds uncovered categories
- Acquisition workflow: dry-run → security gate → quality gate → install → validate
- Developer watch list: add, check for new activity, list
- Report generation: ecosystem, developers, gaps, alerts (saved as JSON)
- Database statistics
- Database pruning with configurable age cutoff
- VACUUM after pruning

#### Infrastructure (common.py)
- Thread-safe SQLite with WAL mode and 30s busy timeout
- Global write lock for concurrent access safety
- Shell wrapper with timeout, JSON parsing, and structured error handling
- stderr-only logging (stdout reserved for JSON output)
- Graceful degradation when CLIs are missing
- SHA-256 content hashing utility

#### Testing
- 29 unit tests covering AST security analysis, regex detection, code metrics, scoring, and CLI parsing
- All tests use stdlib unittest (zero dependencies)
