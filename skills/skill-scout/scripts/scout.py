"""Orchestrator CLI for skill-scout.

Ties discovery and evaluation together into high-level workflows: developer
ranking, skill ranking, gap analysis, acquisition (with security gates),
developer watch lists, ecosystem reporting, and database maintenance.

All output goes to stdout as JSON.  Diagnostic messages use stderr via the
shared logger.
"""

import argparse
import json
import math
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from common import (
    SCOUT_DATA_DIR,
    SKILLS_DIR,
    ShellError,
    check_tool,
    db_read,
    db_write,
    get_db,
    json_out,
    logger,
    run_shell,
    utcnow,
)

# ---------------------------------------------------------------------------
# Developer ranking
# ---------------------------------------------------------------------------

def rank_developers(min_skills: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
    """Rank developers by a weighted composite score.

    Formula:
        Score = (0.40 × AvgQuality) + (0.15 × VolumeLogScaled) +
                (0.15 × Reputation) + (0.15 × Consistency) +
                (0.15 × Freshness)

    Args:
        min_skills: Minimum evaluated skills to be ranked (default 1).
        limit: Maximum developers to return (default 20).

    Returns:
        Ranked list of developer dicts with score breakdown.
    """
    # Get all developers with evaluated skills
    developers = db_read("SELECT * FROM developers WHERE skill_count >= ?",
                         (min_skills,))

    ranked = []
    for dev in developers:
        username = dev["username"]
        raw = json.loads(dev.get("raw_data") or "{}")

        # Quality (40%)
        avg_q = dev.get("avg_skill_quality") or 0
        quality_component = avg_q  # Already 0-100 scale

        # Volume log-scaled (15%) — caps at 20 skills.
        # Log scaling prevents gaming: publishing 50 trivial skills won't
        # outscore someone with 5 excellent ones.  log2(21) ≈ 4.39 is the
        # denominator, so 20 skills = 100%, 5 skills ≈ 58%, 1 skill ≈ 23%.
        skill_count = dev.get("skill_count", 0)
        volume_component = (math.log2(1 + skill_count) / math.log2(1 + 20)) * 100

        # Reputation (15%) — followers + stars + account age
        followers = raw.get("followers", 0)
        total_stars = raw.get("total_stars", 0)
        account_age = raw.get("account_age_days", 0)
        reputation_component = min(100,
            (followers / 100 + total_stars / 1000 + account_age / 365) * 10
        )

        # Consistency (15%) — need multiple skills for std dev
        skills_data = db_read(
            "SELECT quality_score FROM skills WHERE author=? AND quality_score IS NOT NULL",
            (username,)
        )
        scores = [s["quality_score"] for s in skills_data]
        if len(scores) >= 2:
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std_dev = math.sqrt(variance)
            consistency_component = max(0, 100 - std_dev * 2)
        else:
            consistency_component = 50  # Neutral if only 1 skill

        # Freshness (15%)
        last_activity = dev.get("last_activity", "")
        freshness_component = 0
        if last_activity:
            try:
                from datetime import datetime as dt, timezone as tz
                activity = dt.fromisoformat(last_activity.replace("Z", "+00:00"))
                days_ago = (dt.now(tz.utc) - activity).days
                if days_ago <= 7:
                    freshness_component = 100
                elif days_ago <= 30:
                    freshness_component = 75
                elif days_ago <= 90:
                    freshness_component = 50
                elif days_ago <= 180:
                    freshness_component = 25
            except ValueError:
                pass

        # Weighted total
        total = (
            0.40 * quality_component +
            0.15 * volume_component +
            0.15 * reputation_component +
            0.15 * consistency_component +
            0.15 * freshness_component
        )

        # Assign tier
        tier = "Watched"
        if skill_count >= 5 and avg_q >= 85 and freshness_component >= 75:
            tier = "Master"
        elif skill_count >= 3 and avg_q >= 70 and freshness_component >= 50:
            tier = "Expert"
        elif skill_count >= 1 and avg_q >= 60:
            tier = "Contributor"

        ranked.append({
            "username": username,
            "score": round(total, 1),
            "tier": tier,
            "skill_count": skill_count,
            "avg_quality": round(avg_q, 1),
            "breakdown": {
                "quality": round(quality_component, 1),
                "volume": round(volume_component, 1),
                "reputation": round(reputation_component, 1),
                "consistency": round(consistency_component, 1),
                "freshness": round(freshness_component, 1),
            },
        })

        # Update developer record
        db_write(
            "UPDATE developers SET score=?, tier=? WHERE username=?",
            (round(total, 1), tier, username),
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]


# ---------------------------------------------------------------------------
# Skill ranking
# ---------------------------------------------------------------------------

def rank_skills(category: Optional[str] = None,
                min_score: float = 0,
                limit: int = 20) -> List[Dict[str, Any]]:
    """Rank skills by quality score with optional filters.

    Args:
        category: Filter by category (optional).
        min_score: Minimum quality score (default 0).
        limit: Maximum results (default 20).

    Returns:
        Ranked list of skill dicts.
    """
    if category:
        rows = db_read(
            """SELECT slug, source, author, description, category, stars,
                      quality_score, quality_tier, installed, flagged
               FROM skills
               WHERE quality_score IS NOT NULL AND quality_score >= ?
                     AND category LIKE ? AND slug != '__awesome_list_cache__'
               ORDER BY quality_score DESC LIMIT ?""",
            (min_score, f"%{category}%", limit),
        )
    else:
        rows = db_read(
            """SELECT slug, source, author, description, category, stars,
                      quality_score, quality_tier, installed, flagged
               FROM skills
               WHERE quality_score IS NOT NULL AND quality_score >= ?
                     AND slug != '__awesome_list_cache__'
               ORDER BY quality_score DESC LIMIT ?""",
            (min_score, limit),
        )

    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------

def analyze_gaps(our_skills_path: Optional[Path] = None) -> Dict[str, Any]:
    """Compare our installed skills against the ecosystem to find capability gaps.

    Scans our skills directory for _meta.json files to build a coverage map,
    then queries the database for high-scoring skills we don't have.

    Args:
        our_skills_path: Path to our skills directory (defaults to SKILLS_DIR).

    Returns:
        Dict with covered skills, gaps by category, and recommendations.
    """
    skills_path = our_skills_path or SKILLS_DIR

    # Catalog our skills
    our_slugs = set()
    our_skills = []
    if skills_path.is_dir():
        for meta_path in skills_path.glob("*/_meta.json"):
            try:
                meta = json.loads(meta_path.read_text())
                slug = meta.get("slug", meta_path.parent.name)
                our_slugs.add(slug)
                our_skills.append({
                    "slug": slug,
                    "name": meta.get("name", slug),
                    "description": meta.get("description", ""),
                    "tags": meta.get("tags", []),
                })
            except (json.JSONDecodeError, OSError):
                pass

    # Find high-quality external skills we don't have
    placeholders = ",".join("?" for _ in our_slugs) if our_slugs else "'__none__'"
    if our_slugs:
        external = db_read(
            f"""SELECT slug, source, author, description, category, stars,
                       quality_score, quality_tier
                FROM skills
                WHERE quality_score >= 75 AND slug NOT IN ({placeholders})
                      AND slug != '__awesome_list_cache__'
                ORDER BY quality_score DESC LIMIT 50""",
            tuple(our_slugs),
        )
    else:
        external = db_read(
            """SELECT slug, source, author, description, category, stars,
                      quality_score, quality_tier
               FROM skills
               WHERE quality_score >= 75 AND slug != '__awesome_list_cache__'
               ORDER BY quality_score DESC LIMIT 50""",
        )

    # Group by category
    gaps_by_category: Dict[str, List[Dict[str, Any]]] = {}
    for skill in external:
        cat = skill.get("category") or "Uncategorized"
        if cat not in gaps_by_category:
            gaps_by_category[cat] = []
        gaps_by_category[cat].append(dict(skill))

    return {
        "our_skill_count": len(our_skills),
        "our_skills": our_skills,
        "gap_categories": len(gaps_by_category),
        "gaps": [
            {"category": cat, "recommended_skills": skills}
            for cat, skills in sorted(
                gaps_by_category.items(),
                key=lambda x: len(x[1]),
                reverse=True,
            )
        ],
        "total_recommendations": len(external),
    }


# ---------------------------------------------------------------------------
# Acquisition
# ---------------------------------------------------------------------------

def acquire_skill(slug: str, install: bool = False) -> Dict[str, Any]:
    """Evaluate and optionally install a skill with security gates.

    Workflow:
    1. Evaluate quality (must be >= 60)
    2. Run security scan (must have 0 critical flags)
    3. If --install: run ``clawhub install`` or ``gh repo clone``
    4. Validate installed skill structure

    Args:
        slug: Skill slug to acquire.
        install: If True, actually install after passing gates.

    Returns:
        Dict with evaluation results, security findings, and install status.
    """
    from evaluate import evaluate_skill

    logger.info("Evaluating %s for acquisition...", slug)
    result = evaluate_skill(slug)

    output: Dict[str, Any] = {
        "slug": slug,
        "quality_score": result.overall_score,
        "tier": result.tier,
        "security_flags": [asdict(f) for f in result.security_flags],
        "critical_flags": sum(1 for f in result.security_flags if f.severity == "critical"),
        "install_requested": install,
        "installed": False,
        "gate_passed": False,
    }

    # Quality gate
    if result.overall_score < 60:
        output["rejection_reason"] = f"Quality score {result.overall_score} < 60 minimum"
        return output

    # Security gate
    critical = [f for f in result.security_flags if f.severity == "critical"]
    if critical:
        output["rejection_reason"] = (
            f"{len(critical)} critical security flag(s) — BLOCKED. "
            "Review security_flags before proceeding."
        )
        return output

    output["gate_passed"] = True

    if not install:
        output["note"] = "Dry run — gates passed. Use --install to proceed."
        return output

    # Install
    installed = False
    install_method = "none"

    if check_tool("clawhub"):
        try:
            run_shell(["clawhub", "install", slug], timeout=60)
            installed = True
            install_method = "clawhub"
        except ShellError as e:
            logger.warning("clawhub install failed: %s", e)

    if not installed:
        # Fallback: check if we have a GitHub URL
        skill_data = db_read("SELECT source_url FROM skills WHERE slug=?", (slug,))
        if skill_data and skill_data[0].get("source_url"):
            url = skill_data[0]["source_url"]
            try:
                run_shell(["gh", "repo", "clone", url,
                           str(SKILLS_DIR / slug.replace("/", "__"))],
                          timeout=120)
                installed = True
                install_method = "gh_clone"
            except ShellError as e:
                logger.error("GitHub clone failed: %s", e)

    if installed:
        # Validate structure
        install_path = SKILLS_DIR / slug.replace("/", "__")
        skill_md = install_path / "SKILL.md"
        output["installed"] = True
        output["install_method"] = install_method
        output["install_path"] = str(install_path)
        output["has_skill_md"] = skill_md.exists()

        # Update DB
        db_write("UPDATE skills SET installed=1 WHERE slug=?", (slug,))
    else:
        output["rejection_reason"] = "Installation failed — neither clawhub nor gh succeeded"

    return output


# ---------------------------------------------------------------------------
# Watch list
# ---------------------------------------------------------------------------

def watch_add(username: str, reason: str = "") -> Dict[str, Any]:
    """Add a developer to the watch list.

    Args:
        username: GitHub username.
        reason: Why we're watching them.

    Returns:
        Confirmation dict.
    """
    now = utcnow()
    db_write(
        """INSERT INTO developers (username, watched, raw_data)
           VALUES (?, 1, '{}')
           ON CONFLICT(username) DO UPDATE SET watched=1""",
        (username,),
    )
    return {"username": username, "watched": True, "reason": reason, "added_at": now}


def watch_check() -> Dict[str, Any]:
    """Check all watched developers for new activity.

    Queries GitHub for each watched developer's recent repos and
    cross-references against our known skills database.

    Returns:
        Dict with alerts for new skills from watched developers.
    """
    from discover import profile_developer

    watched = db_read("SELECT username FROM developers WHERE watched=1")
    alerts: List[Dict[str, Any]] = []

    for dev in watched:
        username = dev["username"]
        logger.info("Checking watched developer: %s", username)
        profile = profile_developer(username)

        if isinstance(profile, dict) and "error" not in profile:
            new_skills = profile.get("known_skills", [])
            if new_skills:
                alerts.append({
                    "developer": username,
                    "skill_count": len(new_skills),
                    "skills": new_skills,
                })

    return {"watched_count": len(watched), "alerts": alerts, "checked_at": utcnow()}


def watch_list() -> List[Dict[str, Any]]:
    """List all watched developers with their tier and last activity.

    Returns:
        List of watched developer dicts.
    """
    return db_read(
        """SELECT username, tier, score, skill_count, avg_skill_quality,
                  last_activity, watched
           FROM developers WHERE watched=1 ORDER BY score DESC"""
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def generate_report(report_type: str) -> Dict[str, Any]:
    """Generate a JSON report and save it to the scout data directory.

    Args:
        report_type: One of ``ecosystem``, ``developers``, ``gaps``, ``alerts``.

    Returns:
        The generated report dict.
    """
    report: Dict[str, Any] = {}

    if report_type == "ecosystem":
        total = db_read("SELECT COUNT(*) as c FROM skills WHERE slug != '__awesome_list_cache__'")
        by_source = db_read(
            """SELECT source, COUNT(*) as count FROM skills
               WHERE slug != '__awesome_list_cache__' GROUP BY source"""
        )
        by_tier = db_read(
            """SELECT quality_tier, COUNT(*) as count FROM skills
               WHERE quality_tier IS NOT NULL GROUP BY quality_tier"""
        )
        top_skills = rank_skills(limit=20)
        top_devs = rank_developers(limit=10)

        report = {
            "generated_at": utcnow(),
            "total_skills": total[0]["c"] if total else 0,
            "by_source": {r["source"]: r["count"] for r in by_source},
            "by_tier": {r["quality_tier"]: r["count"] for r in by_tier},
            "top_20_skills": top_skills,
            "top_10_developers": top_devs,
        }
        _save_report("ecosystem-report.json", report)

    elif report_type == "developers":
        devs = rank_developers(limit=100)
        report = {
            "generated_at": utcnow(),
            "total_developers": len(devs),
            "developers": devs,
        }
        _save_report("developer-hierarchy.json", report)

    elif report_type == "gaps":
        report = analyze_gaps()
        report["generated_at"] = utcnow()
        _save_report("gap-analysis.json", report)

    elif report_type == "alerts":
        report = watch_check()
        _save_report("watch-alerts.json", report)

    else:
        report = {"error": f"Unknown report type: {report_type}"}

    return report


def _save_report(filename: str, data: Dict[str, Any]) -> None:
    """Save a report as JSON to the scout data directory.

    Args:
        filename: Report filename.
        data: Report data.
    """
    SCOUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = SCOUT_DATA_DIR / filename
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    logger.info("Report saved: %s", path)


# ---------------------------------------------------------------------------
# Database maintenance
# ---------------------------------------------------------------------------

def db_stats() -> Dict[str, Any]:
    """Return database statistics.

    Returns:
        Dict with table counts, tier distribution, and file size.
    """
    skills_count = db_read(
        "SELECT COUNT(*) as c FROM skills WHERE slug != '__awesome_list_cache__'"
    )
    devs_count = db_read("SELECT COUNT(*) as c FROM developers")
    evals_count = db_read("SELECT COUNT(*) as c FROM evaluations")
    by_source = db_read(
        """SELECT source, COUNT(*) as count FROM skills
           WHERE slug != '__awesome_list_cache__' GROUP BY source"""
    )
    by_tier = db_read(
        """SELECT quality_tier, COUNT(*) as count FROM skills
           WHERE quality_tier IS NOT NULL GROUP BY quality_tier"""
    )
    dev_tiers = db_read(
        "SELECT tier, COUNT(*) as count FROM developers WHERE tier IS NOT NULL GROUP BY tier"
    )

    db_size = 0
    from common import DB_PATH
    if DB_PATH.exists():
        db_size = DB_PATH.stat().st_size

    return {
        "total_skills": skills_count[0]["c"] if skills_count else 0,
        "total_developers": devs_count[0]["c"] if devs_count else 0,
        "total_evaluations": evals_count[0]["c"] if evals_count else 0,
        "skills_by_source": {r["source"]: r["count"] for r in by_source},
        "skills_by_tier": {r["quality_tier"]: r["count"] for r in by_tier},
        "developers_by_tier": {r["tier"]: r["count"] for r in dev_tiers},
        "db_size_bytes": db_size,
        "db_path": str(DB_PATH),
    }


def prune_old(days: int = 90) -> Dict[str, Any]:
    """Remove stale records from the database.

    Args:
        days: Remove records not seen in this many days (default 90).

    Returns:
        Dict with counts of removed records.
    """
    from datetime import datetime as dt, timedelta, timezone as tz
    cutoff = (dt.now(tz.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Count before
    before_skills = db_read("SELECT COUNT(*) as c FROM skills")[0]["c"]
    before_evals = db_read("SELECT COUNT(*) as c FROM evaluations")[0]["c"]

    # Delete stale skills (but not installed or flagged ones)
    db_write(
        "DELETE FROM skills WHERE first_seen < ? AND installed=0 AND flagged=0 AND slug != '__awesome_list_cache__'",
        (cutoff,),
    )

    # Delete old evaluations
    db_write("DELETE FROM evaluations WHERE evaluated_at < ?", (cutoff,))

    # VACUUM
    conn = get_db()
    conn.execute("VACUUM")

    after_skills = db_read("SELECT COUNT(*) as c FROM skills")[0]["c"]
    after_evals = db_read("SELECT COUNT(*) as c FROM evaluations")[0]["c"]

    return {
        "cutoff_days": days,
        "skills_removed": before_skills - after_skills,
        "evaluations_removed": before_evals - after_evals,
        "skills_remaining": after_skills,
        "evaluations_remaining": after_evals,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the scout orchestrator CLI."""
    parser = argparse.ArgumentParser(
        description="Skill Scout — orchestrate discovery, evaluation, and acquisition",
        prog="scout.py",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # rank-developers
    p_rd = sub.add_parser("rank-developers", help="Rank developers by composite score")
    p_rd.add_argument("--min-skills", type=int, default=1, help="Min evaluated skills")
    p_rd.add_argument("--limit", type=int, default=20, help="Max results")

    # rank-skills
    p_rs = sub.add_parser("rank-skills", help="Rank skills by quality score")
    p_rs.add_argument("--category", help="Filter by category")
    p_rs.add_argument("--min-score", type=float, default=0, help="Min quality score")
    p_rs.add_argument("--limit", type=int, default=20, help="Max results")

    # gaps
    p_gap = sub.add_parser("gaps", help="Find capability gaps vs ecosystem")
    p_gap.add_argument("--our-skills", help="Path to our skills directory")

    # recommend
    p_rec = sub.add_parser("recommend", help="Recommend skills for a category")
    p_rec.add_argument("--category", required=True, help="Category to search")
    p_rec.add_argument("--limit", type=int, default=5, help="Max recommendations")

    # acquire
    p_acq = sub.add_parser("acquire", help="Evaluate and optionally install a skill")
    p_acq.add_argument("--slug", required=True, help="Skill slug")
    p_acq.add_argument("--install", action="store_true", help="Install after passing gates")
    p_acq.add_argument("--dry-run", action="store_true", help="Evaluate without installing")

    # watch
    p_watch = sub.add_parser("watch", help="Manage developer watch list")
    p_watch.add_argument("--add", help="GitHub username to watch")
    p_watch.add_argument("--reason", default="", help="Reason for watching")
    p_watch.add_argument("--check", action="store_true", help="Check all watched devs")
    p_watch.add_argument("--list", action="store_true", dest="list_watched",
                          help="List watched developers")

    # report
    p_rep = sub.add_parser("report", help="Generate ecosystem reports")
    p_rep.add_argument("--type", required=True,
                        choices=["ecosystem", "developers", "gaps", "alerts"],
                        help="Report type")

    # stats
    sub.add_parser("stats", help="Database statistics")

    # prune
    p_prune = sub.add_parser("prune", help="Remove stale records")
    p_prune.add_argument("--days", type=int, default=90, help="Age cutoff in days")

    args = parser.parse_args()

    if args.command == "rank-developers":
        results = rank_developers(args.min_skills, args.limit)
        json_out({"count": len(results), "developers": results})

    elif args.command == "rank-skills":
        results = rank_skills(args.category, args.min_score, args.limit)
        json_out({"count": len(results), "skills": results})

    elif args.command == "gaps":
        path = Path(args.our_skills) if args.our_skills else None
        result = analyze_gaps(path)
        json_out(result)

    elif args.command == "recommend":
        results = rank_skills(category=args.category, min_score=60, limit=args.limit)
        # Add install commands
        for r in results:
            r["install_cmd"] = f"clawhub install {r['slug']}"
        json_out({"category": args.category, "count": len(results),
                  "recommendations": results})

    elif args.command == "acquire":
        result = acquire_skill(args.slug, install=args.install and not args.dry_run)
        json_out(result)

    elif args.command == "watch":
        if args.add:
            result = watch_add(args.add, args.reason)
            json_out(result)
        elif args.check:
            result = watch_check()
            json_out(result)
        elif args.list_watched:
            results = watch_list()
            json_out({"count": len(results), "watched": results})
        else:
            json_out({"error": "Specify --add, --check, or --list"})

    elif args.command == "report":
        result = generate_report(args.type)
        json_out(result)

    elif args.command == "stats":
        result = db_stats()
        json_out(result)

    elif args.command == "prune":
        result = prune_old(args.days)
        json_out(result)


if __name__ == "__main__":
    main()
