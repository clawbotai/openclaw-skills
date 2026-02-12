"""Batch rename skill directories and update all internal references.

Renames directories, updates _meta.json slugs, and does find-and-replace
across all text files to fix path references.
"""

import json
import os
import re
import shutil
from pathlib import Path

WORKSPACE = Path("/Users/clawai/openclaw/workspace")
SKILLS_DIR = WORKSPACE / "skills"

# Old name -> New name mapping
RENAMES = {
    # Drop "master-" prefix, use descriptive names
    "api-design": "api-design",
    "construction-management": "construction-management",
    "data-engineering": "data-engineering",
    "devops": "devops",
    "docs-engine": "docs-engine",
    "growth-strategy": "growth-strategy",
    "ml-engineering": "ml-engineering",
    "observability": "observability",
    "payments": "payments",
    "performance-engineering": "performance-engineering",
    "qa-engineering": "qa-engineering",
    "security": "security",

    # Drop "sw-" prefix
    "mobile-architect": "mobile-architect",
    "python-backend": "python-backend",

    # Drop "skill-" prefix where it adds nothing
    "skill-evolver": "skill-evolver",
    "skill-monitor": "skill-monitor",

    # More descriptive names
    "task-planner": "task-planner",
    "file-planner": "file-planner",
    "product-management": "product-management",
    "auth-patterns": "auth-patterns",
    "biz-development": "biz-development",
}

def rename_all():
    """Execute all renames."""
    # First pass: collect all text files in workspace for reference updates
    text_files = []
    for ext in ["*.md", "*.py", "*.json", "*.sh", "*.txt", "*.yml", "*.yaml"]:
        text_files.extend(WORKSPACE.rglob(ext))
    # Filter out .git, node_modules, __pycache__
    text_files = [f for f in text_files if not any(
        p in str(f) for p in [".git/", "node_modules/", "__pycache__/", ".clawhub/"]
    )]

    print(f"Found {len(text_files)} text files to scan for references")

    # Second pass: do find-and-replace in all text files
    for old_name, new_name in RENAMES.items():
        old_dir = SKILLS_DIR / old_name
        if not old_dir.exists():
            print(f"SKIP: {old_name} (not found)")
            continue

        # Patterns to replace (order matters — longer patterns first)
        replacements = [
            (f"skills/{old_name}/", f"skills/{new_name}/"),
            (f"skills/{old_name}", f"skills/{new_name}"),
            (f'"{old_name}"', f'"{new_name}"'),  # JSON slug values
            (f"'{old_name}'", f"'{new_name}'"),
        ]

        for tf in text_files:
            if not tf.exists():
                continue
            try:
                content = tf.read_text(encoding="utf-8")
                original = content
                for old_pat, new_pat in replacements:
                    content = content.replace(old_pat, new_pat)
                if content != original:
                    tf.write_text(content, encoding="utf-8")
                    print(f"  Updated refs in: {tf.relative_to(WORKSPACE)}")
            except (UnicodeDecodeError, OSError):
                pass

    # Third pass: rename directories
    for old_name, new_name in RENAMES.items():
        old_dir = SKILLS_DIR / old_name
        new_dir = SKILLS_DIR / new_name
        if not old_dir.exists():
            continue
        if new_dir.exists():
            print(f"ERROR: {new_name} already exists!")
            continue

        # Update _meta.json slug
        meta_path = old_dir / "_meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                if meta.get("slug") == old_name:
                    meta["slug"] = new_name
                    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
            except (json.JSONDecodeError, OSError):
                pass

        # Rename directory
        old_dir.rename(new_dir)
        print(f"RENAMED: {old_name} -> {new_name}")

    print("\nDone!")

if __name__ == "__main__":
    rename_all()
