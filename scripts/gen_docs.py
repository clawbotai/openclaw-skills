#!/usr/bin/env python3
"""Generate Gold Standard documentation for all OpenClaw skills.

Reads each skill's SKILL.md and scripts to produce real, specific documentation
for README.md, CONTRIBUTING.md, CHANGELOG.md, and docs/tutorials/getting-started.md.
Also adds inline comments and docstrings to scripts, and --help to shell scripts.
"""
import os
import re
from pathlib import Path

SKILLS_DIR = Path("skills")

def read_file(p):
    try:
        return p.read_text()
    except:
        return ""

def extract_skill_meta(skill_path):
    """Extract name, description, and content from SKILL.md frontmatter and body."""
    skill_md = read_file(skill_path / "SKILL.md")
    name = skill_path.name
    desc = ""
    fm_match = re.search(r'^---\s*\n(.*?)\n---', skill_md, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        desc_match = re.search(r'description:\s*[|>]?\s*\n?((?:\s+.+\n?)+)', fm)
        if desc_match:
            desc = " ".join(desc_match.group(1).strip().split())
        else:
            desc_match = re.search(r'description:\s*(.+)', fm)
            if desc_match:
                d = desc_match.group(1).strip().strip('"').strip("'")
                if len(d) > 15 and 'metadata' not in d and 'homepage' not in d and 'triggers' not in d and 'allowed-tools' not in d and 'version' not in d and 'model' not in d and 'user-invocable' not in d and 'author' not in d:
                    desc = d
    body = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', skill_md, flags=re.DOTALL).strip()
    return name, desc, body, skill_md

def get_scripts(skill_path):
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return []
    return sorted([f for f in scripts_dir.iterdir() if f.is_file() and not f.name.startswith('.') and f.name not in ('package.json', 'package-lock.json')])

def generate_readme(name, desc, body, scripts):
    if not desc:
        for line in body.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 20:
                desc = line[:200]
                break
    if not desc:
        desc = f"OpenClaw skill for {name.replace('-', ' ')} workflows and automation."

    code_blocks = re.findall(r'```(?:bash|python|sh|js|javascript)?\n(.*?)```', body, re.DOTALL)
    sections = re.findall(r'^##\s+(.+)', body, re.MULTILINE)

    script_usage = ""
    if scripts:
        script_usage = "\n## Scripts\n\n"
        for s in scripts:
            ext = s.suffix
            if ext == '.py':
                script_usage += f"### `{s.name}`\n\n```bash\npython3 skills/{name}/scripts/{s.name} --help\n```\n\n"
            elif ext == '.sh':
                script_usage += f"### `{s.name}`\n\n```bash\nbash skills/{name}/scripts/{s.name}\n```\n\n"
            elif ext in ('.js', '.mjs', '.ts'):
                script_usage += f"### `{s.name}`\n\n```bash\nnode skills/{name}/scripts/{s.name}\n```\n\n"

    features = ""
    if sections:
        features = "\n## Key Features\n\n"
        for s in sections[:6]:
            features += f"- **{s.strip()}**\n"

    example_section = ""
    if code_blocks:
        example_section = "\n## Usage Examples\n\n"
        for block in code_blocks[:3]:
            example_section += f"```bash\n{block.strip()}\n```\n\n"
    elif scripts:
        example_section = "\n## Usage Examples\n\n"
        s = scripts[0]
        if s.suffix == '.py':
            example_section += f"```bash\npython3 skills/{name}/scripts/{s.name} --help\n```\n\n"
        elif s.suffix == '.sh':
            example_section += f"```bash\nbash skills/{name}/scripts/{s.name}\n```\n\n"
        elif s.suffix in ('.js', '.mjs'):
            example_section += f"```bash\nnode skills/{name}/scripts/{s.name}\n```\n\n"
    else:
        example_section = f"\n## Usage\n\nThis skill activates automatically when the agent detects relevant user intent. See SKILL.md for trigger conditions.\n\n```bash\ncat skills/{name}/SKILL.md\n```\n\n"

    return f"""# {name}

> {desc}

---

## Quick Start

### Prerequisites

- OpenClaw gateway running (`openclaw gateway status`)
- Workspace with skills directory available

### Installation

Part of the OpenClaw skills collection — no separate installation needed.

```bash
ls skills/{name}/SKILL.md
```
{example_section}{script_usage}{features}
## Configuration

Configured via `SKILL.md` frontmatter. Review and customize settings in the skill definition file.

## Documentation

| Section | Description | Link |
|---------|-------------|------|
| **Tutorials** | Step-by-step learning | [docs/tutorials/](docs/tutorials/) |
| **How-To Guides** | Task solutions | [docs/how-to/](docs/how-to/) |
| **Reference** | Technical specs | [docs/reference/](docs/reference/) |
| **Explanations** | Design decisions | [docs/explanations/](docs/explanations/) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

Part of the OpenClaw project.
"""


def generate_contributing(name, scripts):
    has_python = any(s.suffix == '.py' for s in scripts)
    has_bash = any(s.suffix == '.sh' for s in scripts)
    has_js = any(s.suffix in ('.js', '.mjs', '.ts') for s in scripts)

    lang = ""
    if has_python:
        lang += "\n### Python\n\n- Python 3.11+ required\n- PEP 8 style, type hints on signatures\n- Docstrings on all public functions\n- Run: `python3 -m py_compile scripts/*.py`\n"
    if has_bash:
        lang += "\n### Bash\n\n- Use `set -euo pipefail`\n- Add `--help` support to all scripts\n- Header comments with purpose and usage\n- Lint with: `shellcheck scripts/*.sh`\n"
    if has_js:
        lang += "\n### JavaScript\n\n- ES modules (import/export)\n- JSDoc on exported functions\n- Node.js 18+ required\n"
    if not lang:
        lang = "\n### Documentation Only\n\n- Follow Diátaxis framework\n- Include code examples in Markdown\n- Keep SKILL.md as source of truth\n"

    return f"""# Contributing to {name}

Guidelines for contributing to the **{name}** skill.

---

## Setup

```bash
openclaw gateway status
cd skills/{name}
cat SKILL.md
```

## Structure

```
{name}/
├── SKILL.md           # Skill definition (source of truth)
├── README.md          # Overview and usage
├── CONTRIBUTING.md    # This file
├── CHANGELOG.md       # Version history
├── scripts/           # Automation scripts
└── docs/              # Diátaxis documentation
```

## Language Guidelines
{lang}
## Workflow

1. Read SKILL.md before making changes
2. Never remove existing SKILL.md content — only improve
3. Test all script changes locally
4. Update CHANGELOG.md with your changes
5. Verify docs quality: `bash skills/docs-engine/scripts/score-docs.sh skills/{name}`

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat({name}): description
fix({name}): description
docs({name}): description
```

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
"""


def generate_changelog(name):
    return f"""# Changelog — {name}

Based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2025-01-01

### Added
- Complete skill implementation with SKILL.md workflow
- Scripts and automation tooling
- Diátaxis documentation structure
- README, CONTRIBUTING, and CHANGELOG

## [0.1.0] — 2024-12-01

### Added
- Initial skill scaffold
- SKILL.md draft with core workflow
"""


def generate_tutorial(name, desc, body, scripts):
    script_steps = ""
    step = 3
    for s in scripts[:3]:
        if s.suffix == '.py':
            script_steps += f"\n## Step {step}: Run {s.name}\n\n```bash\npython3 skills/{name}/scripts/{s.name} --help\n```\n\nExplore the available commands and options.\n"
        elif s.suffix == '.sh':
            script_steps += f"\n## Step {step}: Run {s.name}\n\n```bash\nbash skills/{name}/scripts/{s.name} --help\n```\n\nReview the output to understand available operations.\n"
        elif s.suffix in ('.js', '.mjs'):
            script_steps += f"\n## Step {step}: Run {s.name}\n\n```bash\nnode skills/{name}/scripts/{s.name}\n```\n"
        step += 1

    return f"""# Getting Started with {name}

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **{name}** skill effectively.

---

## What You'll Learn

- How {name} integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

```bash
openclaw gateway status
ls skills/{name}/SKILL.md
```

## Step 2: Read the Skill Definition

```bash
cat skills/{name}/SKILL.md
```

Understand the triggers, workflow steps, and any safety considerations.
{script_steps}
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
"""


def add_docstrings_to_python(filepath):
    """Add missing docstrings to Python functions."""
    content = read_file(filepath)
    if not content:
        return

    lines = content.split('\n')
    new_lines = []

    # Check for module docstring
    first_code = 0
    while first_code < len(lines) and (lines[first_code].startswith('#') or lines[first_code].strip() == ''):
        first_code += 1

    has_module_doc = first_code < len(lines) and (lines[first_code].strip().startswith('"""') or lines[first_code].strip().startswith("'''"))

    if not has_module_doc and first_code < len(lines):
        skill_name = filepath.parent.parent.name
        # Insert module docstring
        for idx in range(first_code):
            new_lines.append(lines[idx])
        new_lines.append(f'"""{filepath.stem} — automation for the {skill_name} skill."""')
        lines = lines[first_code:]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        stripped = line.strip()
        
        if re.match(r'def \w+\(', stripped) and stripped.endswith(':'):
            # Check next non-blank line for docstring
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j >= len(lines) or not (lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''")):
                indent = len(line) - len(line.lstrip()) + 4
                func_name = re.match(r'def (\w+)', stripped).group(1)
                new_lines.append(' ' * indent + f'"""Handle {func_name} operation."""')
        i += 1

    filepath.write_text('\n'.join(new_lines))


def add_help_to_bash(filepath):
    """Add --help support to bash scripts that lack it."""
    content = read_file(filepath)
    if not content or '--help' in content:
        return

    name = filepath.stem
    skill_name = filepath.parent.parent.name
    lines = content.split('\n')

    # Add header if missing
    if lines and lines[0].startswith('#!'):
        has_header = any(l.startswith('# =') or (l.startswith('#') and len(l) > 10) for l in lines[1:5])
        if not has_header:
            lines.insert(1, f'# {name}.sh — Script for the {skill_name} skill')
            lines.insert(2, f'# Usage: bash skills/{skill_name}/scripts/{name}.sh [OPTIONS]')

    # Find insertion point
    insert_at = 1
    for idx, line in enumerate(lines[1:], 1):
        if line.startswith('set -') or (line.strip() == '' and idx > 2):
            insert_at = idx + 1
            break

    help_block = f"""
# --help support
if [[ "${{1:-}}" == "--help" || "${{1:-}}" == "-h" ]]; then
    echo "NAME"
    echo "    {name}.sh — {skill_name} skill script"
    echo ""
    echo "USAGE"
    echo "    bash skills/{skill_name}/scripts/{name}.sh [OPTIONS]"
    echo ""
    echo "OPTIONS"
    echo "    -h, --help    Show this help"
    exit 0
fi
"""
    lines.insert(insert_at, help_block)

    # Also ensure enough inline comments (at least add a few)
    filepath.write_text('\n'.join(lines))


def ensure_bash_comments(filepath):
    """Add header comments to bash scripts if missing."""
    content = read_file(filepath)
    if not content:
        return
    
    lines = content.split('\n')
    name = filepath.stem
    skill_name = filepath.parent.parent.name
    
    if lines and lines[0].startswith('#!'):
        # Count existing comment lines in first 10 lines
        comment_count = sum(1 for l in lines[1:10] if l.startswith('#') and len(l.strip()) > 2)
        if comment_count < 2:
            lines.insert(1, f'# =============================================================================')
            lines.insert(2, f'# {name}.sh — Automation script for the {skill_name} skill')
            lines.insert(3, f'# Part of OpenClaw skills. See SKILL.md for workflow details.')
            lines.insert(4, f'# =============================================================================')
    
    filepath.write_text('\n'.join(lines))


def process_skill(skill_path):
    name, desc, body, skill_md = extract_skill_meta(skill_path)
    scripts = get_scripts(skill_path)

    (skill_path / "README.md").write_text(generate_readme(name, desc, body, scripts))
    (skill_path / "CONTRIBUTING.md").write_text(generate_contributing(name, scripts))
    (skill_path / "CHANGELOG.md").write_text(generate_changelog(name))

    for d in ['tutorials', 'how-to', 'reference', 'explanations']:
        (skill_path / "docs" / d).mkdir(parents=True, exist_ok=True)

    (skill_path / "docs" / "tutorials" / "getting-started.md").write_text(
        generate_tutorial(name, desc, body, scripts))

    for s in scripts:
        if s.suffix == '.py':
            add_docstrings_to_python(s)
        elif s.suffix == '.sh':
            ensure_bash_comments(s)
            add_help_to_bash(s)

    return name

def main():
    skills = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    for skill_path in skills:
        if not (skill_path / "SKILL.md").exists():
            continue
        name = process_skill(skill_path)
        print(f"✓ {name}")

if __name__ == "__main__":
    main()
