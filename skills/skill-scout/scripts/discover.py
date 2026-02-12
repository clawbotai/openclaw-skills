"""Discovery engine for skill-scout.

Searches ClawHub, GitHub, and curated awesome lists to find OpenClaw skills
and their developers.  All network access is delegated to ``clawhub`` and
``gh`` CLIs via subprocess; no direct HTTP calls are made.

Uses ``concurrent.futures.ThreadPoolExecutor`` for parallel discovery across
multiple categories, and implements a circuit-breaker pattern that falls back
to cached database results after three consecutive CLI failures.
"""

import argparse
import base64
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from common import (
    DB_PATH,
    ShellError,
    check_tool,
    db_read,
    db_write,
    db_write_many,
    get_db,
    json_out,
    logger,
    run_shell,
    utcnow,
)

# ---------------------------------------------------------------------------
# Circuit breaker — gives up after N consecutive failures per tool
# ---------------------------------------------------------------------------

# Circuit breaker pattern: if a CLI tool fails N times consecutively, stop
# calling it and return cached DB results instead.  This prevents cascading
# failures when a tool is down (e.g. GitHub rate limited, clawhub offline)
# and avoids wasting time on retries that will likely fail.  The breaker
# resets on any successful call, so transient failures self-heal.
_BREAKER_THRESHOLD = 3
_failure_counts: Dict[str, int] = {"clawhub": 0, "gh": 0}


def _record_failure(tool: str) -> None:
    """Increment the failure counter for a CLI tool.

    Args:
        tool: Tool name (``clawhub`` or ``gh``).
    """
    _failure_counts[tool] = _failure_counts.get(tool, 0) + 1
    if _failure_counts[tool] >= _BREAKER_THRESHOLD:
        logger.warning("Circuit breaker OPEN for %s after %d failures",
                       tool, _failure_counts[tool])


def _record_success(tool: str) -> None:
    """Reset the failure counter for a CLI tool after a successful call.

    Args:
        tool: Tool name.
    """
    _failure_counts[tool] = 0


def _breaker_open(tool: str) -> bool:
    """Check whether the circuit breaker is open (tripped) for a tool.

    Args:
        tool: Tool name.

    Returns:
        True if the tool has failed >= threshold times consecutively.
    """
    return _failure_counts.get(tool, 0) >= _BREAKER_THRESHOLD


# ---------------------------------------------------------------------------
# ClawHub discovery
# ---------------------------------------------------------------------------

# clawhub search outputs a text table, not JSON.  Each result line looks like:
#   calendar v1.0.0  Calendar  (0.520)
# The first line is always a spinner ("- Searching") which we skip.
# We capture: slug, version, display name, and relevance score.
_CLAWHUB_LINE_RE = re.compile(
    r"^(\S+)\s+v([\d.]+)\s+(.+?)\s+\(([\d.]+)\)\s*$"
)


def _parse_clawhub_search(output: str) -> List[Dict[str, Any]]:
    """Parse the text output of ``clawhub search``.

    The format is: ``<slug> v<version>  <name>  (<score>)``
    Lines that don't match (e.g. the spinner ``- Searching``) are skipped.

    Args:
        output: Raw stdout from ``clawhub search``.

    Returns:
        List of dicts with keys: slug, version, name, relevance.
    """
    results: List[Dict[str, Any]] = []
    for line in output.strip().splitlines():
        line = line.strip()
        m = _CLAWHUB_LINE_RE.match(line)
        if m:
            results.append({
                "slug": m.group(1),
                "version": m.group(2),
                "name": m.group(3).strip(),
                "relevance": float(m.group(4)),
            })
    return results


def search_clawhub(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search the ClawHub registry for skills matching a query.

    Args:
        query: Natural-language search query.
        limit: Maximum number of results (default 20).

    Returns:
        List of skill dicts persisted to the database, or cached results
        if the circuit breaker is open.
    """
    if _breaker_open("clawhub"):
        logger.info("ClawHub breaker open — returning cached results for '%s'", query)
        return db_read(
            "SELECT * FROM skills WHERE source='clawhub' AND description LIKE ?",
            (f"%{query}%",)
        )

    try:
        out = run_shell(["clawhub", "search", query, "--limit", str(limit)],
                        timeout=30)
        _record_success("clawhub")
    except ShellError as e:
        _record_failure("clawhub")
        logger.error("clawhub search failed: %s", e)
        return db_read(
            "SELECT * FROM skills WHERE source='clawhub' AND description LIKE ?",
            (f"%{query}%",)
        )

    parsed = _parse_clawhub_search(out["stdout"])
    now = utcnow()

    for skill in parsed:
        # Try to get richer metadata via inspect --json
        meta = _inspect_clawhub(skill["slug"])
        stars = 0
        downloads = 0
        description = skill["name"]
        author = ""
        if meta:
            stats = meta.get("skill", {}).get("stats", {})
            stars = stats.get("stars", 0)
            downloads = stats.get("downloads", 0)
            description = meta.get("skill", {}).get("summary", skill["name"])
            author = meta.get("owner", {}).get("handle", "")

        db_write(
            """INSERT INTO skills (slug, source, author, version, description,
                    stars, downloads, first_seen, raw_data)
               VALUES (?, 'clawhub', ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET
                    version=excluded.version, description=excluded.description,
                    stars=excluded.stars, downloads=excluded.downloads,
                    author=excluded.author, raw_data=excluded.raw_data""",
            (skill["slug"], author, skill["version"], description,
             stars, downloads, now, json.dumps(meta) if meta else None),
        )

    return db_read(
        "SELECT * FROM skills WHERE slug IN ({})".format(
            ",".join("?" for _ in parsed)
        ),
        tuple(s["slug"] for s in parsed),
    ) if parsed else []


def _inspect_clawhub(slug: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed metadata for a skill from ClawHub.

    Args:
        slug: The skill slug.

    Returns:
        Parsed JSON metadata dict, or None on failure.
    """
    try:
        out = run_shell(["clawhub", "inspect", slug, "--json"], timeout=20)
        return out.get("json")
    except ShellError:
        return None


# ---------------------------------------------------------------------------
# GitHub discovery
# ---------------------------------------------------------------------------

def search_github(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search GitHub for repositories matching a query.

    Uses ``gh api search/repositories`` and extracts repository metadata
    including owner, stars, forks, description, and last push date.

    Args:
        query: GitHub search query string.
        limit: Maximum results (default 20).

    Returns:
        List of skill dicts persisted to the database, or cached results
        if the circuit breaker is open.
    """
    if _breaker_open("gh"):
        logger.info("GitHub breaker open — returning cached results for '%s'", query)
        return db_read(
            "SELECT * FROM skills WHERE source='github' AND description LIKE ?",
            (f"%{query}%",)
        )

    try:
        out = run_shell([
            "gh", "api", "search/repositories",
            "-f", f"q={query}",
            "-f", "sort=stars",
            "-f", f"per_page={limit}",
        ], timeout=30)
        _record_success("gh")
    except ShellError as e:
        _record_failure("gh")
        logger.error("GitHub search failed: %s", e)
        return db_read(
            "SELECT * FROM skills WHERE source='github' AND description LIKE ?",
            (f"%{query}%",)
        )

    data = out.get("json", {})
    items = data.get("items", [])
    now = utcnow()
    results: List[Dict[str, Any]] = []

    for repo in items:
        slug = repo.get("full_name", "").replace("/", "__")
        author = repo.get("owner", {}).get("login", "")
        source_url = repo.get("html_url", "")
        description = (repo.get("description") or "")[:500]
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        pushed = repo.get("pushed_at", "")

        db_write(
            """INSERT INTO skills (slug, source, source_url, author, description,
                    stars, forks, last_updated, first_seen, raw_data)
               VALUES (?, 'github', ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET
                    source_url=excluded.source_url, description=excluded.description,
                    stars=excluded.stars, forks=excluded.forks,
                    last_updated=excluded.last_updated, raw_data=excluded.raw_data""",
            (slug, source_url, author, description, stars, forks, pushed,
             now, json.dumps(repo)),
        )
        results.append({
            "slug": slug, "source": "github", "author": author,
            "description": description, "stars": stars, "forks": forks,
            "source_url": source_url,
        })

    return results


def fetch_github_file(owner: str, repo: str, path: str) -> Optional[str]:
    """Fetch a single file's raw content from a GitHub repository.

    Args:
        owner: Repository owner (username or org).
        repo: Repository name.
        path: File path within the repo.

    Returns:
        Raw file content as a string, or None on failure.
    """
    try:
        out = run_shell([
            "gh", "api",
            f"repos/{owner}/{repo}/contents/{path}",
            "-H", "Accept: application/vnd.github.raw",
        ], timeout=20)
        return out["stdout"]
    except ShellError:
        return None


# ---------------------------------------------------------------------------
# Awesome-list discovery
# ---------------------------------------------------------------------------

_AWESOME_ENTRY_RE = re.compile(
    r"-\s+\[([^\]]+)\]\((https://github\.com/[^)]+)\)\s*-?\s*(.*)"
)
_AWESOME_CACHE_KEY = "awesome_list_last_fetched"


def parse_awesome_list(refresh: bool = False) -> Dict[str, Any]:
    """Parse the VoltAgent awesome-openclaw-skills README into categorized skills.

    Fetches the README from GitHub, parses markdown category headers and
    skill entries, and stores each skill in the database.  Results are
    cached — pass ``refresh=True`` to force a re-fetch.

    Args:
        refresh: If True, ignore cache and re-fetch from GitHub.

    Returns:
        Dict with ``categories`` (list of name+count dicts) and
        ``total_skills`` count.
    """
    if _breaker_open("gh"):
        logger.info("GitHub breaker open — returning cached awesome list")
        rows = db_read("SELECT * FROM skills WHERE source='awesome-list'")
        return {"total_skills": len(rows), "categories": [], "cached": True}

    # Check cache (stored as a skill record with special slug)
    if not refresh:
        cached = db_read(
            "SELECT raw_data FROM skills WHERE slug='__awesome_list_cache__'"
        )
        if cached and cached[0].get("raw_data"):
            try:
                cache = json.loads(cached[0]["raw_data"])
                # Re-fetch if older than 24 hours
                from datetime import datetime as dt
                fetched = dt.fromisoformat(cache.get("fetched_at", "2000-01-01T00:00:00Z").replace("Z", "+00:00"))
                from datetime import timezone as tz
                age_hours = (dt.now(tz.utc) - fetched).total_seconds() / 3600
                if age_hours < 24:
                    logger.info("Using cached awesome list (%.1fh old)", age_hours)
                    return cache.get("result", {"total_skills": 0, "categories": []})
            except (ValueError, KeyError):
                pass

    # Fetch README
    try:
        out = run_shell([
            "gh", "api",
            "repos/VoltAgent/awesome-openclaw-skills/contents/README.md",
            "-H", "Accept: application/vnd.github.raw",
        ], timeout=30)
        _record_success("gh")
    except ShellError as e:
        _record_failure("gh")
        logger.error("Failed to fetch awesome list: %s", e)
        rows = db_read("SELECT * FROM skills WHERE source='awesome-list'")
        return {"total_skills": len(rows), "categories": [], "error": str(e)}

    readme = out["stdout"]
    categories: Dict[str, List[Dict[str, str]]] = {}
    current_category = "Uncategorized"
    now = utcnow()

    # The awesome list README is structured markdown with:
    #   ### Category Name (count)   — section headers
    #   - [name](url) - description — skill entries
    # We parse both patterns with regex rather than importing a markdown
    # library, keeping our zero-dependency constraint.
    batch_params = []  # Collect for batch insert

    for line in readme.splitlines():
        # Detect category headers (### Category Name)
        header_match = re.match(r"^###\s+(.+?)(?:\s*\(.*\))?\s*$", line)
        if header_match:
            current_category = header_match.group(1).strip()
            if current_category not in categories:
                categories[current_category] = []
            continue

        # Detect skill entries
        entry_match = _AWESOME_ENTRY_RE.match(line.strip())
        if entry_match:
            name = entry_match.group(1).strip()
            url = entry_match.group(2).strip()
            desc = entry_match.group(3).strip()

            # Extract slug from URL: github.com/openclaw/skills/tree/.../slug/SKILL.md
            slug_match = re.search(r"/skills/(.+?)(?:/SKILL\.md)?$", url)
            slug = slug_match.group(1) if slug_match else name.lower().replace(" ", "-")
            # Extract author from slug if it has a path like author/skill
            author = ""
            if "/" in slug:
                parts = slug.split("/")
                author = parts[0] if len(parts) >= 2 else ""

            if current_category not in categories:
                categories[current_category] = []
            categories[current_category].append({
                "slug": slug, "name": name, "url": url, "description": desc,
            })

            batch_params.append(
                (slug, url, author, desc, current_category, now)
            )

    # Batch write all awesome list entries at once
    if batch_params:
        db_write_many(
            """INSERT INTO skills (slug, source, source_url, author, description,
                    category, first_seen)
               VALUES (?, 'awesome-list', ?, ?, ?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET
                    source_url=excluded.source_url, category=excluded.category,
                    description=excluded.description""",
            batch_params,
        )

    result = {
        "total_skills": sum(len(v) for v in categories.values()),
        "categories": [
            {"name": k, "count": len(v)} for k, v in categories.items()
            if k not in ("Uncategorized",) or v  # skip empty uncategorized
        ],
    }

    # Cache the result
    db_write(
        """INSERT INTO skills (slug, source, first_seen, raw_data)
           VALUES ('__awesome_list_cache__', 'cache', ?, ?)
           ON CONFLICT(slug) DO UPDATE SET raw_data=excluded.raw_data""",
        (now, json.dumps({"fetched_at": now, "result": result})),
    )

    return result


# ---------------------------------------------------------------------------
# Developer profiles
# ---------------------------------------------------------------------------

def profile_developer(username: str) -> Dict[str, Any]:
    """Build a developer profile from GitHub data and cross-reference with known skills.

    Args:
        username: GitHub username.

    Returns:
        Dict with developer profile data.
    """
    if _breaker_open("gh"):
        cached = db_read("SELECT * FROM developers WHERE username=?", (username,))
        if cached:
            return cached[0]
        return {"username": username, "error": "GitHub breaker open, no cached data"}

    # Fetch user profile
    try:
        user_out = run_shell(["gh", "api", f"users/{username}"], timeout=20)
        _record_success("gh")
    except ShellError as e:
        _record_failure("gh")
        return {"username": username, "error": str(e)}

    user = user_out.get("json", {})
    followers = user.get("followers", 0)
    created_at = user.get("created_at", "")

    # Fetch repos
    repos: List[str] = []
    total_stars = 0
    try:
        repos_out = run_shell([
            "gh", "api", f"users/{username}/repos",
            "-f", "per_page=100", "-f", "sort=stars",
            "--jq", ".[].full_name",
        ], timeout=20)
        repos = [r for r in repos_out["stdout"].strip().splitlines() if r]

        # Get total stars
        stars_out = run_shell([
            "gh", "api", f"users/{username}/repos",
            "-f", "per_page=100",
            "--jq", "[.[].stargazers_count] | add",
        ], timeout=20)
        total_stars = int(stars_out["stdout"].strip() or "0")
    except (ShellError, ValueError):
        pass

    # Cross-reference with known skills
    known_skills = db_read(
        "SELECT slug, quality_score FROM skills WHERE author=?", (username,)
    )
    skill_count = len(known_skills)
    scores = [s["quality_score"] for s in known_skills if s["quality_score"] is not None]
    avg_quality = sum(scores) / len(scores) if scores else 0.0

    # Calculate account age in days
    account_age_days = 0
    if created_at:
        try:
            from datetime import datetime as dt, timezone as tz
            created = dt.fromisoformat(created_at.replace("Z", "+00:00"))
            account_age_days = (dt.now(tz.utc) - created).days
        except ValueError:
            pass

    now = utcnow()
    profile = {
        "username": username,
        "followers": followers,
        "total_stars": total_stars,
        "account_age_days": account_age_days,
        "repos": repos[:20],
        "skill_count": skill_count,
        "avg_skill_quality": round(avg_quality, 1),
        "known_skills": [s["slug"] for s in known_skills],
    }

    db_write(
        """INSERT INTO developers (username, skill_count, avg_skill_quality,
                last_activity, raw_data)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(username) DO UPDATE SET
                skill_count=excluded.skill_count,
                avg_skill_quality=excluded.avg_skill_quality,
                last_activity=excluded.last_activity,
                raw_data=excluded.raw_data""",
        (username, skill_count, round(avg_quality, 1), now, json.dumps(profile)),
    )

    return profile


# ---------------------------------------------------------------------------
# Multi-category sweep
# ---------------------------------------------------------------------------

def sweep_categories(categories: List[str], limit_per: int = 10) -> Dict[str, Any]:
    """Run parallel discovery across multiple categories.

    Uses a ThreadPoolExecutor with up to 5 workers.  Each category triggers
    both a ClawHub and a GitHub search.  Results are deduplicated by slug.

    Args:
        categories: List of category keyword strings.
        limit_per: Max results per category per source (default 10).

    Returns:
        Dict with per-category counts and a ``total`` skill count.
    """
    has_clawhub = check_tool("clawhub") and not _breaker_open("clawhub")
    has_gh = check_tool("gh") and not _breaker_open("gh")

    results: Dict[str, int] = {}

    # Each category is searched independently in its own thread.
    # We search both ClawHub (vector search, fast, curated) and GitHub
    # (broader, catches non-registry repos) for maximum coverage.
    def _search_category(cat: str) -> Tuple[str, int]:
        """Search a single category across available sources.

        Runs inside a ThreadPoolExecutor worker. All exceptions are caught
        to prevent a single category failure from poisoning the thread or
        leaving DB connections in a bad state.

        Args:
            cat: Category keyword.

        Returns:
            Tuple of (category, result_count).
        """
        count = 0
        try:
            if has_clawhub:
                try:
                    r = search_clawhub(cat, limit=limit_per)
                    count += len(r)
                except Exception as e:
                    logger.error("ClawHub sweep error for '%s': %s", cat, e)

            if has_gh:
                try:
                    r = search_github(f"openclaw {cat} skill", limit=limit_per)
                    count += len(r)
                except Exception as e:
                    logger.error("GitHub sweep error for '%s': %s", cat, e)
        except Exception as e:
            # Catch-all: prevent thread from dying with uncaught exception
            logger.error("Unexpected error in sweep worker for '%s': %s", cat, e)

        return cat, count

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_search_category, c): c for c in categories}
        for future in as_completed(futures):
            try:
                cat, count = future.result()
                results[cat] = count
            except Exception as e:
                cat = futures[future]
                logger.error("Sweep failed for '%s': %s", cat, e)
                results[cat] = 0

    return {
        "categories": results,
        "total": sum(results.values()),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the discover CLI."""
    parser = argparse.ArgumentParser(
        description="Discover OpenClaw skills across ClawHub, GitHub, and awesome lists",
        prog="discover.py",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # clawhub
    p_ch = sub.add_parser("clawhub", help="Search ClawHub registry")
    p_ch.add_argument("--query", required=True, help="Search query")
    p_ch.add_argument("--limit", type=int, default=20, help="Max results")

    # github
    p_gh = sub.add_parser("github", help="Search GitHub repositories")
    p_gh.add_argument("--query", required=True, help="Search query")
    p_gh.add_argument("--limit", type=int, default=20, help="Max results")

    # awesome
    p_aw = sub.add_parser("awesome", help="Parse VoltAgent awesome list")
    p_aw.add_argument("--refresh", action="store_true", help="Force re-fetch")

    # developer
    p_dev = sub.add_parser("developer", help="Build a developer profile")
    p_dev.add_argument("--username", required=True, help="GitHub username")

    # sweep
    p_sw = sub.add_parser("sweep", help="Multi-category parallel discovery")
    p_sw.add_argument("--categories", required=True,
                       help="Comma-separated category keywords")
    p_sw.add_argument("--limit", type=int, default=10, help="Results per category")

    args = parser.parse_args()

    if args.command == "clawhub":
        if not check_tool("clawhub"):
            json_out({"error": "clawhub CLI not found on PATH"})
            sys.exit(1)
        results = search_clawhub(args.query, args.limit)
        json_out({"query": args.query, "source": "clawhub", "count": len(results),
                  "skills": results})

    elif args.command == "github":
        if not check_tool("gh"):
            json_out({"error": "gh CLI not found on PATH"})
            sys.exit(1)
        results = search_github(args.query, args.limit)
        json_out({"query": args.query, "source": "github", "count": len(results),
                  "skills": results})

    elif args.command == "awesome":
        result = parse_awesome_list(refresh=args.refresh)
        json_out(result)

    elif args.command == "developer":
        profile = profile_developer(args.username)
        json_out(profile)

    elif args.command == "sweep":
        cats = [c.strip() for c in args.categories.split(",") if c.strip()]
        result = sweep_categories(cats, args.limit)
        json_out(result)


if __name__ == "__main__":
    main()
