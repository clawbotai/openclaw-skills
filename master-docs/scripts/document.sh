#!/usr/bin/env bash
# =============================================================================
# document.sh — Main documentation dispatcher
#
# Routes documentation tasks to the appropriate mode: inline analysis, reference
# generation, help injection, project overview, or quality scoring.
# This script itself serves as a demonstration of good --help output.
# =============================================================================

set -euo pipefail

# --- Constants ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="1.0.0"

# =============================================================================
# Help — Standard POSIX-style help output
# =============================================================================

show_help() {
    cat <<'EOF'
NAME
    document.sh — auto-generate documentation for any codebase

SYNOPSIS
    document.sh [OPTIONS] <path> <mode>

DESCRIPTION
    Analyzes a project or skill directory and generates documentation based on
    the selected mode. Supports multiple programming languages (detected from
    file extensions) and outputs human-readable results.

    This is the main entry point for the master-docs skill. For focused tasks,
    you can also use inject-help.sh or score-docs.sh directly.

MODES
    inline      Analyze files and report which need inline documentation.
                Lists files by language with comment coverage statistics.

    reference   Scan for public functions/commands and generate a reference
                document skeleton in Markdown format.

    help        Find all shell scripts and inject --help support using
                inject-help.sh. Equivalent to running inject-help.sh directly.

    overview    Generate a project overview skeleton (architecture, components,
                data flow) based on directory structure analysis.

    score       Run the documentation quality auditor. Equivalent to running
                score-docs.sh directly.

OPTIONS
    -h, --help      Show this help message and exit
    -v, --verbose   Enable verbose output (show per-file details)
    -o, --output    Write output to a file instead of stdout
    --version       Show version and exit

EXAMPLES
    document.sh ./my-project score
        Run a documentation quality audit on my-project.

    document.sh ./skills/auth-patterns inline
        Analyze the auth skill for inline documentation coverage.

    document.sh -o docs/reference.md ./src reference
        Generate a function reference skeleton and save to a file.

    document.sh ./scripts help
        Inject --help into all shell scripts under ./scripts.

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

# --- Validate required args ---
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

# Resolve to absolute path
TARGET="$(cd "$TARGET" 2>/dev/null && pwd || realpath "$TARGET")"

# =============================================================================
# Utility Functions
# =============================================================================

# Detect programming languages present in a directory by file extension
detect_languages() {
    local dir="$1"
    find "$dir" -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.js" -o -name "*.ts" \
        -o -name "*.tsx" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" -o -name "*.rs" \
        -o -name "*.rb" -o -name "*.java" -o -name "*.md" \) 2>/dev/null \
        | sed 's/.*\.//' | sort | uniq -c | sort -rn
}

# Count comment lines vs total lines for a file
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

# Redirect output if -o was specified
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
        -o -name "*.go" -o -name "*.rs" -o -name "*.rb" -o -name "*.java" \) 2>/dev/null | sort)

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
    sh_files=$(find "$TARGET" -type f \( -name "*.sh" -o -name "*.bash" \) 2>/dev/null | sort)
    if [[ -n "$sh_files" ]]; then
        echo "## Shell Functions"
        echo ""
        while IFS= read -r file; do
            local rel="${file#$TARGET/}"
            # Extract function definitions
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
    py_files=$(find "$TARGET" -type f -name "*.py" 2>/dev/null | sort)
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
    js_files=$(find "$TARGET" -type f \( -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" \) 2>/dev/null | sort)
    if [[ -n "$js_files" ]]; then
        echo "## JavaScript/TypeScript Functions"
        echo ""
        while IFS= read -r file; do
            local rel="${file#$TARGET/}"
            grep -n '^\s*\(export \)\?\(async \)\?\(function\|const\|let\) ' "$file" 2>/dev/null | \
                grep -v 'node_modules' | head -50 | while IFS=: read -r line_num match; do
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

    # Description from README if available
    if [[ -f "$TARGET/README.md" ]]; then
        echo "## Description"
        echo ""
        head -20 "$TARGET/README.md" | grep -v '^#' | head -5
        echo ""
    fi

    echo "## Directory Structure"
    echo ""
    echo "\`\`\`"
    # Show top 2 levels, exclude hidden dirs and node_modules
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
    for f in README.md SKILL.md AGENTS.md _meta.json package.json setup.py Cargo.toml go.mod; do
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
# Mode: score — Run documentation quality audit
# =============================================================================

mode_score() {
    bash "$SCRIPT_DIR/score-docs.sh" "$TARGET"
}

# =============================================================================
# Dispatch
# =============================================================================

case "$MODE" in
    inline)    mode_inline ;;
    reference) mode_reference ;;
    help)      mode_help ;;
    overview)  mode_overview ;;
    score)     mode_score ;;
    *)
        echo "Error: Unknown mode '$MODE'." >&2
        echo "Valid modes: inline, reference, help, overview, score" >&2
        exit 1
        ;;
esac
