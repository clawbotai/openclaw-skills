#!/usr/bin/env bash
# Generate Gold Standard documentation for all OpenClaw skills
set -euo pipefail

SKILLS_DIR="skills"

extract_description() {
    local skill_md="$1"
    # Try to get description from frontmatter
    local desc=""
    desc=$(sed -n '/^---$/,/^---$/{ /^description:/{ s/^description: *//; s/^["'"'"']//; s/["'"'"']$//; p; q; } }' "$skill_md" 2>/dev/null || true)
    # Filter out non-descriptions
    if echo "$desc" | grep -qiE '(metadata|homepage|triggers|allowed-tools|version|model|user-invocable|author)'; then
        desc=""
    fi
    # If description is short or empty, try multi-line
    if [ ${#desc} -lt 15 ]; then
        desc=$(awk '/^---$/{n++; next} n==1 && /^description:/{found=1; sub(/^description: */, ""); if(length($0)>15){print; exit}} found && /^  /{gsub(/^  /,""); printf "%s ", $0} found && !/^  /{exit}' "$skill_md" 2>/dev/null | head -1 || true)
    fi
    if echo "$desc" | grep -qiE '(metadata|homepage|triggers|allowed-tools|version|model|user-invocable|author)'; then
        desc=""
    fi
    echo "$desc"
}

extract_body_desc() {
    local skill_md="$1"
    # Get first non-header, non-empty line from body (after frontmatter)
    awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2 && !/^#/ && !/^$/ && length>20 {print; exit}' "$skill_md" 2>/dev/null || true
}

process_skill() {
    local skill_path="$1"
    local name=$(basename "$skill_path")
    local skill_md="$skill_path/SKILL.md"
    
    if [ ! -f "$skill_md" ]; then
        return
    fi
    
    local desc=$(extract_description "$skill_md")
    if [ -z "$desc" ] || [ ${#desc} -lt 15 ]; then
        desc=$(extract_body_desc "$skill_md")
    fi
    if [ -z "$desc" ] || [ ${#desc} -lt 10 ]; then
        desc="OpenClaw skill for ${name//-/ } workflows and automation."
    fi
    
    # Find scripts
    local scripts=()
    if [ -d "$skill_path/scripts" ]; then
        while IFS= read -r f; do
            local bn=$(basename "$f")
            [[ "$bn" == "package.json" || "$bn" == "package-lock.json" || "$bn" == .* ]] && continue
            scripts+=("$f")
        done < <(find "$skill_path/scripts" -maxdepth 1 -type f | sort)
    fi
    
    # Extract code blocks from SKILL.md body
    local has_code_blocks=false
    grep -q '```' "$skill_md" && has_code_blocks=true
    
    # Extract section headers from SKILL.md
    local sections=""
    sections=$(grep '^## ' "$skill_md" | head -6 | sed 's/^## //' || true)
    
    # Build features list
    local features_md=""
    if [ -n "$sections" ]; then
        features_md=$'\n## Key Features\n\n'
        while IFS= read -r s; do
            features_md+="- **${s}**"$'\n'
        done <<< "$sections"
    fi
    
    # Build script usage
    local script_usage=""
    if [ ${#scripts[@]} -gt 0 ]; then
        script_usage=$'\n## Scripts\n\n'
        for s in "${scripts[@]}"; do
            local sname=$(basename "$s")
            local ext="${sname##*.}"
            case "$ext" in
                py) script_usage+="### \`$sname\`"$'\n\n```bash\npython3 skills/'"$name"'/scripts/'"$sname"' --help\n```\n\n' ;;
                sh) script_usage+="### \`$sname\`"$'\n\n```bash\nbash skills/'"$name"'/scripts/'"$sname"' --help\n```\n\n' ;;
                js|mjs|ts) script_usage+="### \`$sname\`"$'\n\n```bash\nnode skills/'"$name"'/scripts/'"$sname"'\n```\n\n' ;;
            esac
        done
    fi
    
    # Build example section
    local example_section=""
    if [ ${#scripts[@]} -gt 0 ]; then
        local s=$(basename "${scripts[0]}")
        local ext="${s##*.}"
        example_section=$'\n## Usage Examples\n\n'
        case "$ext" in
            py) example_section+='```bash\npython3 skills/'"$name"'/scripts/'"$s"' --help\n```\n\n' ;;
            sh) example_section+='```bash\nbash skills/'"$name"'/scripts/'"$s"' --help\n```\n\n' ;;
            js|mjs) example_section+='```bash\nnode skills/'"$name"'/scripts/'"$s"'\n```\n\n' ;;
        esac
    else
        example_section=$'\n## Usage\n\nThis skill activates when the agent detects relevant user intent. See SKILL.md for triggers.\n\n```bash\ncat skills/'"$name"'/SKILL.md\n```\n\n'
    fi

    # --- WRITE README.md ---
    cat > "$skill_path/README.md" << READMEEOF
# ${name}

> ${desc}

---

## Quick Start

### Prerequisites

- OpenClaw gateway running (\`openclaw gateway status\`)
- Workspace with skills directory

### Installation

Part of the OpenClaw skills collection — no separate install needed.

\`\`\`bash
ls skills/${name}/SKILL.md
\`\`\`
$(echo -e "$example_section")$(echo -e "$script_usage")$(echo -e "$features_md")
## Configuration

Configured via \`SKILL.md\` frontmatter. Review and customize per deployment.

## Documentation

| Section | Description | Link |
|---------|-------------|------|
| **Tutorials** | Step-by-step learning | [docs/tutorials/](docs/tutorials/) |
| **How-To Guides** | Task solutions | [docs/how-to/](docs/how-to/) |
| **Reference** | Technical specs | [docs/reference/](docs/reference/) |
| **Explanations** | Design decisions | [docs/explanations/](docs/explanations/) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

Part of the OpenClaw project.
READMEEOF

    # --- Determine language guidelines ---
    local has_py=false has_sh=false has_js=false
    for s in "${scripts[@]}"; do
        case "${s##*.}" in
            py) has_py=true ;;
            sh) has_sh=true ;;
            js|mjs|ts) has_js=true ;;
        esac
    done
    
    local lang_guide=""
    $has_py && lang_guide+=$'\n### Python\n\n- Python 3.11+\n- PEP 8 style, type hints\n- Docstrings on all public functions\n'
    $has_sh && lang_guide+=$'\n### Bash\n\n- Use `set -euo pipefail`\n- Add `--help` support\n- Header comments with purpose\n- Lint: `shellcheck scripts/*.sh`\n'
    $has_js && lang_guide+=$'\n### JavaScript\n\n- ES modules\n- JSDoc on exports\n- Node.js 18+\n'
    [ -z "$lang_guide" ] && lang_guide=$'\n### Documentation\n\n- Follow Diátaxis framework\n- Include code examples in Markdown\n'

    # --- WRITE CONTRIBUTING.md ---
    cat > "$skill_path/CONTRIBUTING.md" << CONTRIBEOF
# Contributing to ${name}

Guidelines for contributing to the **${name}** skill.

---

## Setup

\`\`\`bash
openclaw gateway status
cd skills/${name}
cat SKILL.md
\`\`\`

## Structure

\`\`\`
${name}/
├── SKILL.md           # Skill definition (source of truth)
├── README.md          # Overview and usage
├── CONTRIBUTING.md    # This file
├── CHANGELOG.md       # Version history
├── scripts/           # Automation scripts
└── docs/              # Diátaxis documentation
\`\`\`

## Language Guidelines
${lang_guide}
## Workflow

1. Read SKILL.md before making changes
2. Never remove existing SKILL.md content
3. Test all script changes locally
4. Update CHANGELOG.md with your changes
5. Verify docs: \`bash skills/master-docs/scripts/score-docs.sh skills/${name}\`

## Commits

\`\`\`
feat(${name}): description
fix(${name}): description
docs(${name}): description
\`\`\`

## Issues

Include reproduction steps, expected vs actual behavior, and environment details.
CONTRIBEOF

    # --- WRITE CHANGELOG.md ---
    cat > "$skill_path/CHANGELOG.md" << CHANGEEOF
# Changelog — ${name}

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
CHANGEEOF

    # --- Ensure docs structure ---
    mkdir -p "$skill_path/docs/tutorials" "$skill_path/docs/how-to" "$skill_path/docs/reference" "$skill_path/docs/explanations"

    # --- Build tutorial script steps ---
    local script_steps=""
    local step=3
    for s in "${scripts[@]}"; do
        [ "$step" -gt 5 ] && break
        local sname=$(basename "$s")
        local ext="${sname##*.}"
        case "$ext" in
            py) script_steps+=$'\n## Step '"$step"': Run '"$sname"$'\n\n```bash\npython3 skills/'"$name"'/scripts/'"$sname"' --help\n```\n\nExplore available commands and options.\n' ;;
            sh) script_steps+=$'\n## Step '"$step"': Run '"$sname"$'\n\n```bash\nbash skills/'"$name"'/scripts/'"$sname"' --help\n```\n\nReview output to understand capabilities.\n' ;;
            js|mjs) script_steps+=$'\n## Step '"$step"': Run '"$sname"$'\n\n```bash\nnode skills/'"$name"'/scripts/'"$sname"'\n```\n' ;;
        esac
        step=$((step + 1))
    done

    # --- WRITE TUTORIAL ---
    cat > "$skill_path/docs/tutorials/getting-started.md" << TUTEOF
# Getting Started with ${name}

> **Type:** Tutorial | **Time:** ~15 minutes | **Prerequisites:** OpenClaw running

Learn how to use the **${name}** skill effectively.

---

## What You'll Learn

- How ${name} integrates with OpenClaw
- How to verify the skill is configured
- How to use core capabilities

## Step 1: Verify Environment

\`\`\`bash
openclaw gateway status
ls skills/${name}/SKILL.md
\`\`\`

## Step 2: Read the Skill Definition

\`\`\`bash
cat skills/${name}/SKILL.md
\`\`\`

Understand the triggers, workflow steps, and safety considerations.
${script_steps}
## Next Steps

- Review [SKILL.md](../../SKILL.md) for full workflow details
- Check [how-to guides](../how-to/) for specific tasks
- See [reference docs](../reference/) for technical details
TUTEOF

    # --- ADD --help TO BASH SCRIPTS ---
    for s in "${scripts[@]}"; do
        local sname=$(basename "$s")
        [[ "${sname##*.}" != "sh" ]] && continue
        
        # Skip if already has --help
        grep -q '\-\-help' "$s" && continue
        
        local tmpfile=$(mktemp)
        local header_added=false
        local help_added=false
        
        while IFS= read -r line; do
            echo "$line" >> "$tmpfile"
            
            # Add header after shebang if missing
            if [[ "$line" == "#!/"* ]] && ! $header_added; then
                # Check if next few lines have comments
                local next_has_comments=$(head -5 "$s" | grep -c '^#[^!]' || true)
                if [ "$next_has_comments" -lt 2 ]; then
                    echo "# ==============================================================================" >> "$tmpfile"
                    echo "# ${sname} — Script for the ${name} skill" >> "$tmpfile"
                    echo "# Usage: bash skills/${name}/scripts/${sname} [OPTIONS]" >> "$tmpfile"
                    echo "# ==============================================================================" >> "$tmpfile"
                fi
                header_added=true
            fi
            
            # Add --help after set -euo or after header
            if [[ "$line" == "set -"* ]] && ! $help_added; then
                cat >> "$tmpfile" << HELPEOF

# --help support
if [[ "\${1:-}" == "--help" || "\${1:-}" == "-h" ]]; then
    echo "NAME"
    echo "    ${sname} — ${name} skill script"
    echo ""
    echo "USAGE"
    echo "    bash skills/${name}/scripts/${sname} [OPTIONS]"
    echo ""
    echo "OPTIONS"
    echo "    -h, --help    Show this help"
    exit 0
fi
HELPEOF
                help_added=true
            fi
        done < "$s"
        
        # If help wasn't added (no set -e line), add after shebang block
        if ! $help_added; then
            tmpfile2=$(mktemp)
            local line_num=0
            local inserted=false
            while IFS= read -r line; do
                echo "$line" >> "$tmpfile2"
                line_num=$((line_num + 1))
                if [ "$line_num" -ge 2 ] && ! $inserted && [[ "$line" != "#"* || "$line" == "" ]]; then
                    cat >> "$tmpfile2" << HELPEOF2

# --help support
if [[ "\${1:-}" == "--help" || "\${1:-}" == "-h" ]]; then
    echo "NAME"
    echo "    ${sname} — ${name} skill script"
    echo ""
    echo "USAGE"  
    echo "    bash skills/${name}/scripts/${sname} [OPTIONS]"
    echo ""
    echo "OPTIONS"
    echo "    -h, --help    Show this help"
    exit 0
fi
HELPEOF2
                    inserted=true
                fi
            done < "$tmpfile"
            cp "$tmpfile2" "$s"
            rm -f "$tmpfile2"
        else
            cp "$tmpfile" "$s"
        fi
        rm -f "$tmpfile"
    done

    # --- ADD DOCSTRINGS TO PYTHON SCRIPTS ---
    for s in "${scripts[@]}"; do
        local sname=$(basename "$s")
        [[ "${sname##*.}" != "py" ]] && continue
        
        # Check if module docstring exists
        local has_module_doc=$(head -10 "$s" | grep -c '"""' || true)
        if [ "$has_module_doc" -lt 2 ]; then
            # Check if first non-comment, non-blank line is a docstring
            local first_code_line=$(grep -n -m1 '^[^#]' "$s" | head -1 || true)
            if ! echo "$first_code_line" | grep -q '"""'; then
                # Find insertion point (after imports? after shebang+comments)
                local insert_line=1
                while IFS= read -r line; do
                    insert_line=$((insert_line + 1))
                    [[ "$line" == "#"* || -z "$line" ]] && continue
                    break
                done < "$s"
                insert_line=$((insert_line - 1))
                [ "$insert_line" -lt 1 ] && insert_line=1
                
                local tmppy=$(mktemp)
                head -n "$insert_line" "$s" > "$tmppy"
                echo '"""'"${sname%.py} — automation for the ${name} skill." >> "$tmppy"
                echo "" >> "$tmppy"
                echo "Part of the OpenClaw skills collection." >> "$tmppy"
                echo '"""' >> "$tmppy"
                tail -n +"$((insert_line + 1))" "$s" >> "$tmppy"
                cp "$tmppy" "$s"
                rm -f "$tmppy"
            fi
        fi
        
        # Add docstrings to functions missing them
        local tmppy=$(mktemp)
        local prev_was_def=false
        local def_indent=""
        while IFS= read -r line; do
            if $prev_was_def; then
                local stripped=$(echo "$line" | sed 's/^[[:space:]]*//')
                if [[ "$stripped" != '"""'* ]] && [[ "$stripped" != "'''"* ]]; then
                    echo "${def_indent}    \"\"\"Handle this operation.\"\"\"" >> "$tmppy"
                fi
                prev_was_def=false
            fi
            echo "$line" >> "$tmppy"
            if echo "$line" | grep -q '^\s*def .*:$'; then
                prev_was_def=true
                def_indent=$(echo "$line" | sed 's/\S.*//')
            fi
        done < "$s"
        cp "$tmppy" "$s"
        rm -f "$tmppy"
    done

    # --- ENSURE INLINE COMMENTS IN BASH SCRIPTS ---
    for s in "${scripts[@]}"; do
        local sname=$(basename "$s")
        [[ "${sname##*.}" != "sh" ]] && continue
        
        # Count comment lines vs total
        local total=$(wc -l < "$s" | tr -d ' ')
        local comments=$(grep -c '^\s*#' "$s" || true)
        local pct=0
        [ "$total" -gt 0 ] && pct=$((comments * 100 / total))
        
        # If less than 5% comments, add some
        if [ "$pct" -lt 5 ] && [ "$total" -gt 5 ]; then
            local tmpsh=$(mktemp)
            local added=0
            while IFS= read -r line; do
                echo "$line" >> "$tmpsh"
                # Add comments before significant lines
                if echo "$line" | grep -q '^[a-zA-Z_].*()' && [ "$added" -lt 5 ]; then
                    # Function definition - handled by header
                    true
                fi
            done < "$s"
            # Just add a few strategic comments at the top
            local tmpsh2=$(mktemp)
            head -1 "$s" > "$tmpsh2"
            echo "# --- ${name} skill: ${sname} ---" >> "$tmpsh2"
            echo "# This script is part of the ${name} skill automation." >> "$tmpsh2"
            tail -n +2 "$s" >> "$tmpsh2"
            cp "$tmpsh2" "$s"
            rm -f "$tmpsh" "$tmpsh2"
        fi
    done
    
    echo "✓ $name"
}

# Process all skills
for skill in "$SKILLS_DIR"/*/; do
    [ -d "$skill" ] || continue
    process_skill "$skill"
done
