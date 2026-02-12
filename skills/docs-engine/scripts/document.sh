#!/usr/bin/env bash
# =============================================================================
# document.sh — Documentation engine dispatcher (v2.0)
#
# Routes documentation tasks to the appropriate mode: scaffold, inline,
# reference, help injection, overview, or quality scoring.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="2.0.0"

# =============================================================================
# Help
# =============================================================================


show_help() {
    cat <<'EOF'
NAME
    document.sh — documentation engine for the GitHub Gold Standard

SYNOPSIS
    document.sh [OPTIONS] <path> <mode>

DESCRIPTION
    Analyzes, scaffolds, and scores project documentation. Version 2.0
    introduces the 'scaffold' mode which creates a complete Diátaxis-based
    documentation structure from templates.

MODES
    scaffold    Create the Gold Standard documentation structure:
                README.md, CONTRIBUTING.md, CHANGELOG.md, and
                docs/{tutorials,how-to,reference,explanations}.
                Never overwrites existing files.

    inline      Analyze files and report inline comment coverage.
                Lists files by language with comment percentage.

    reference   Scan for public functions/commands and generate a
                reference document skeleton in Markdown.

    help        Inject --help support into shell scripts.

    overview    Generate a project overview skeleton based on
                directory structure analysis.

    score       Run the documentation quality auditor (v2.0 stricter
                scoring with Gold Standard checks).

OPTIONS
    -h, --help      Show this help message and exit
    -v, --verbose   Enable verbose output (show per-file details)
    -o, --output    Write output to a file instead of stdout
    --version       Show version and exit

EXAMPLES
    document.sh ./my-project scaffold
        Create the full Gold Standard docs structure.

    document.sh ./my-project score
        Run a strict documentation quality audit.

    document.sh -o docs/reference/api.md ./src reference
        Generate function reference and save to file.

    document.sh ./scripts help
        Inject --help into all shell scripts.

EXIT STATUS
    0   Success
    1   General error or missing arguments
    2   Target path does not exist
EOF
}

# =============================================================================
# Argument Parsing
# =============================================================================

VERBOSE=0
OUTPUT=""
TARGET=""
MODE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)    show_help; exit 0 ;;
        --version)    echo "document.sh v${VERSION}"; exit 0 ;;
        -v|--verbose) VERBOSE=1; shift ;;
        -o|--output)  OUTPUT="$2"; shift 2 ;;
        -*)           echo "Error: Unknown option '$1'. Use --help for usage." >&2; exit 1 ;;
        *)
            if [[ -z "$TARGET" ]]; then
                TARGET="$1"
            elif [[ -z "$MODE" ]]; then
                MODE="$1"
            else
                echo "Error: Unexpected argument '$1'. Use --help for usage." >&2; exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$TARGET" || -z "$MODE" ]]; then
    echo "Error: Both <path> and <mode> are required." >&2
    echo "Usage: document.sh [OPTIONS] <path> <mode>" >&2
    echo "Try 'document.sh --help' for more information." >&2
    exit 1
fi

if [[ ! -e "$TARGET" ]]; then
    echo "Error: Path '$TARGET' does not exist." >&2
    exit 2
fi

TARGET="$(cd "$TARGET" 2>/dev/null && pwd || realpath "$TARGET")"

# =============================================================================
# Utility Functions
# =============================================================================


detect_languages() {
    local dir="$1"
    find "$dir" -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.js" -o -name "*.ts" \
        -o -name "*.tsx" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" -o -name "*.rs" \
        -o -name "*.rb" -o -name "*.java" -o -name "*.md" \) \
        -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null \
        | sed 's/.*\.//' | sort | uniq -c | sort -rn
}


comment_ratio() {
    local file="$1"
    local ext="${file##*.}"
    local total comment_lines
    total=$(wc -l < "$file" 2>/dev/null || echo 0)
    [[ "$total" -eq 0 ]] && echo "0" && return
    case "$ext" in
        sh|bash|py|rb)
            comment_lines=$(grep -c '^\s*#' "$file" 2>/dev/null || echo 0) ;;
        js|ts|tsx|jsx|go|rs|java)
            comment_lines=$(grep -c '^\s*\(//\|/\*\|\*\)' "$file" 2>/dev/null || echo 0) ;;
        *)
            comment_lines=0 ;;
    esac
    echo "$((comment_lines * 100 / total))"
}


output_start() {
    if [[ -n "$OUTPUT" ]]; then
        exec 3>&1
        exec > "$OUTPUT"
    fi
}


output_end() {
    if [[ -n "$OUTPUT" ]]; then
        exec >&3
        echo "Output written to: $OUTPUT"
    fi
}

# =============================================================================
# Mode: scaffold — Create Gold Standard documentation structure
# =============================================================================


mode_scaffold() {
    local project_name
    project_name=$(basename "$TARGET")
    local created=0
    local skipped=0

    echo "╔═══════════════════════════════════════════════════╗"
    echo "║  Documentation Scaffold — Gold Standard v2.0     ║"
    echo "║  Target: $project_name"
    echo "╚═══════════════════════════════════════════════════╝"
    echo ""

    # --- Diátaxis directory structure ---
    echo "── Diátaxis Directory Structure ──"
    for dir in docs/tutorials docs/how-to docs/reference docs/explanations; do
        if [[ -d "$TARGET/$dir" ]]; then
            echo "  ✓ $dir/ (exists)"
            skipped=$((skipped + 1))
        else
            mkdir -p "$TARGET/$dir"
            echo "  + $dir/ (created)"
            created=$((created + 1))
        fi
    done
    echo ""

    # --- Root documentation files ---
    echo "── Root Documentation Files ──"

    # README.md
    if [[ -f "$TARGET/README.md" ]]; then
        echo "  ✓ README.md (exists — not overwriting)"
        skipped=$((skipped + 1))
    else
        sed "s/\[Project Name\]/$project_name/g; s/\[project-name\]/$project_name/g" \
            "$SKILL_DIR/templates/README.md" > "$TARGET/README.md"
        echo "  + README.md (created from template)"
        created=$((created + 1))
    fi

    # CONTRIBUTING.md
    if [[ -f "$TARGET/CONTRIBUTING.md" ]]; then
        echo "  ✓ CONTRIBUTING.md (exists — not overwriting)"
        skipped=$((skipped + 1))
    else
        sed "s/\[Project Name\]/$project_name/g" \
            "$SKILL_DIR/templates/CONTRIBUTING.md" > "$TARGET/CONTRIBUTING.md"
        echo "  + CONTRIBUTING.md (created from template)"
        created=$((created + 1))
    fi

    # CHANGELOG.md
    if [[ -f "$TARGET/CHANGELOG.md" ]]; then
        echo "  ✓ CHANGELOG.md (exists — not overwriting)"
        skipped=$((skipped + 1))
    else
        sed "s/\[Project Name\]/$project_name/g" \
            "$SKILL_DIR/templates/CHANGELOG.md" > "$TARGET/CHANGELOG.md"
        echo "  + CHANGELOG.md (created from template)"
        created=$((created + 1))
    fi
    echo ""

    # --- Starter docs inside Diátaxis folders ---
    echo "── Starter Documentation ──"

    # Tutorial starter
    if [[ -f "$TARGET/docs/tutorials/getting-started.md" ]]; then
        echo "  ✓ docs/tutorials/getting-started.md (exists)"
        skipped=$((skipped + 1))
    else
        sed "s/\[Project Name\]/$project_name/g" \
            "$SKILL_DIR/templates/docs/tutorials/getting-started.md" > "$TARGET/docs/tutorials/getting-started.md"
        echo "  + docs/tutorials/getting-started.md (created)"
        created=$((created + 1))
    fi

    # .gitkeep files for empty dirs
    for dir in how-to reference explanations; do
        local target_dir="$TARGET/docs/$dir"
        if [[ -z "$(ls -A "$target_dir" 2>/dev/null)" ]]; then
            touch "$target_dir/.gitkeep"
            echo "  + docs/$dir/.gitkeep (placeholder)"
        fi
    done
    echo ""

    # --- Summary ---
    echo "── Summary ──"
    echo "  Created: $created"
    echo "  Skipped (already exist): $skipped"
    echo ""

    if [[ "$created" -gt 0 ]]; then
        echo "  Next steps:"
        echo "    1. Edit README.md — replace [TODO] placeholders with real content"
        echo "    2. Edit CONTRIBUTING.md — customize for your project"
        echo "    3. Write your first tutorial in docs/tutorials/getting-started.md"
        echo "    4. Run: document.sh $TARGET score  (check your progress)"
    else
        echo "  All Gold Standard files already exist. Run 'score' to check quality."
    fi
}

# =============================================================================
# Mode: inline — Analyze inline documentation coverage
# =============================================================================


mode_inline() {
    output_start
    echo "# Inline Documentation Analysis"
    echo "# Target: $TARGET"
    echo "# $(date)"
    echo ""

    echo "## Languages Detected"
    echo ""
    detect_languages "$TARGET"
    echo ""

    echo "## File-by-File Comment Coverage"
    echo ""
    printf "%-60s %s\n" "FILE" "COMMENT %"
    printf "%-60s %s\n" "----" "---------"

    local total_files=0
    local well_documented=0

    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        local ratio
        ratio=$(comment_ratio "$file")
        local rel_path="${file#$TARGET/}"
        printf "%-60s %s%%\n" "$rel_path" "$ratio"
        total_files=$((total_files + 1))
        [[ "$ratio" -ge 10 ]] && well_documented=$((well_documented + 1))
    done < <(find "$TARGET" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.ts" \
        -o -name "*.go" -o -name "*.rs" -o -name "*.rb" -o -name "*.java" \) \
        -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null | sort)

    echo ""
    if [[ "$total_files" -gt 0 ]]; then
        echo "## Summary"
        echo "  Files analyzed: $total_files"
        echo "  Well-documented (≥10% comments): $well_documented / $total_files"
        echo "  Coverage: $((well_documented * 100 / total_files))%"
    else
        echo "No source files found."
    fi
    output_end
}

# =============================================================================
# Mode: reference — Generate function reference skeleton
# =============================================================================


mode_reference() {
    output_start
    echo "# Function Reference"
    echo ""
    echo "> Auto-generated from: $TARGET"
    echo "> Date: $(date)"
    echo ""

    # Shell functions
    local sh_files
    sh_files=$(find "$TARGET" -type f \( -name "*.sh" -o -name "*.bash" \) \
        -not -path '*/node_modules/*' 2>/dev/null | sort)
    if [[ -n "$sh_files" ]]; then
        echo "## Shell Functions"
        echo ""
        while IFS= read -r file; do
            local rel="${file#$TARGET/}"
            grep -n '^\s*\([a-zA-Z_][a-zA-Z0-9_]*\)\s*()\s*{' "$file" 2>/dev/null | while IFS=: read -r line_num match; do
                local func_name
                func_name=$(echo "$match" | sed 's/\s*().*//; s/^\s*//')
                echo "### \`$func_name\` ($rel:$line_num)"
                echo ""
                echo "**Description:** TODO"
                echo ""
                echo "**Example:**"
                echo "\`\`\`bash"
                echo "$func_name"
                echo "\`\`\`"
                echo ""
            done
        done <<< "$sh_files"
    fi

    # Python functions
    local py_files
    py_files=$(find "$TARGET" -type f -name "*.py" \
        -not -path '*/node_modules/*' -not -path '*/__pycache__/*' 2>/dev/null | sort)
    if [[ -n "$py_files" ]]; then
        echo "## Python Functions"
        echo ""
        while IFS= read -r file; do
            local rel="${file#$TARGET/}"
            grep -n '^\s*def ' "$file" 2>/dev/null | while IFS=: read -r line_num match; do
                local func_sig
                func_sig=$(echo "$match" | sed 's/^\s*//' | sed 's/:\s*$//')
                echo "### \`$func_sig\` ($rel:$line_num)"
                echo ""
                echo "**Description:** TODO"
                echo ""
                echo "**Example:**"
                echo "\`\`\`python"
                echo "# TODO: add example"
                echo "\`\`\`"
                echo ""
            done
        done <<< "$py_files"
    fi

    # JS/TS functions
    local js_files
    js_files=$(find "$TARGET" -type f \( -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" \) \
        -not -path '*/node_modules/*' 2>/dev/null | sort)
    if [[ -n "$js_files" ]]; then
        echo "## JavaScript/TypeScript Functions"
        echo ""
        while IFS= read -r file; do
            local rel="${file#$TARGET/}"
            grep -n '^\s*\(export \)\?\(async \)\?\(function\|const\|let\) ' "$file" 2>/dev/null | \
                head -50 | while IFS=: read -r line_num match; do
                local sig
                sig=$(echo "$match" | sed 's/^\s*//' | cut -c1-80)
                echo "### \`$sig\` ($rel:$line_num)"
                echo ""
                echo "**Description:** TODO"
                echo ""
            done
        done <<< "$js_files"
    fi

    output_end
}

# =============================================================================
# Mode: help — Inject --help into shell scripts
# =============================================================================


mode_help() {
    echo "Injecting --help support into shell scripts in: $TARGET"
    echo ""
    bash "$SCRIPT_DIR/inject-help.sh" "$TARGET"
}

# =============================================================================
# Mode: overview — Generate project overview skeleton
# =============================================================================


mode_overview() {
    output_start
    local project_name
    project_name=$(basename "$TARGET")

    echo "# $project_name — Project Overview"
    echo ""
    echo "> Auto-generated on $(date). Edit and expand as needed."
    echo ""

    if [[ -f "$TARGET/README.md" ]]; then
        echo "## Description"
        echo ""
        head -20 "$TARGET/README.md" | grep -v '^#' | grep -v '^\[!\[' | head -5
        echo ""
    fi

    echo "## Directory Structure"
    echo ""
    echo "\`\`\`"
    find "$TARGET" -maxdepth 2 -not -path '*/\.*' -not -path '*/node_modules/*' | \
        sed "s|$TARGET|$project_name|" | head -40
    echo "\`\`\`"
    echo ""

    echo "## Languages & File Types"
    echo ""
    detect_languages "$TARGET"
    echo ""

    echo "## Key Files"
    echo ""
    for f in README.md SKILL.md AGENTS.md _meta.json package.json setup.py pyproject.toml Cargo.toml go.mod Makefile; do
        [[ -f "$TARGET/$f" ]] && echo "- \`$f\` — $(head -1 "$TARGET/$f" | sed 's/^#\s*//')"
    done
    echo ""

    echo "## Components"
    echo ""
    echo "TODO: Describe the main components and how they interact."
    echo ""

    echo "## Data Flow"
    echo ""
    echo "TODO: Describe how data moves through the system."
    echo ""

    echo "## Getting Started"
    echo ""
    echo "TODO: Steps to set up and run this project."
    output_end
}

# =============================================================================
# Mode: score — Documentation quality audit (v2.0)
# =============================================================================


mode_score() {
    bash "$SCRIPT_DIR/score-docs.sh" "$TARGET"
}

# =============================================================================
# Dispatch
# =============================================================================

case "$MODE" in
    scaffold)  mode_scaffold ;;
    inline)    mode_inline ;;
    reference) mode_reference ;;
    help)      mode_help ;;
    overview)  mode_overview ;;
    score)     mode_score ;;
    *)
        echo "Error: Unknown mode '$MODE'." >&2
        echo "Valid modes: scaffold, inline, reference, help, overview, score" >&2
        exit 1
        ;;
esac
