#!/usr/bin/env bash
# =============================================================================
# score-docs.sh — Documentation quality auditor
#
# Scans a project directory and scores its documentation health (0-100).
# Checks for README, inline comments, docstrings, --help support, and more.
# Exit codes reflect quality: 0 (≥80), 1 (50-79), 2 (<50).
# =============================================================================

set -euo pipefail

VERSION="1.0.0"

show_help() {
    cat <<'EOF'
NAME
    score-docs.sh — documentation quality auditor

SYNOPSIS
    score-docs.sh [OPTIONS] <path>

DESCRIPTION
    Scans a project or skill directory and produces a documentation quality
    score from 0 to 100, with specific improvement suggestions.

    Checks performed:
      - README.md exists and has content          (15 points)
      - README quality (description, examples)    (10 points)
      - Inline comment ratio in source files      (20 points)
      - Docstrings / JSDoc in functions            (20 points)
      - Shell scripts support --help               (15 points)
      - CHANGELOG.md exists                        (5 points)
      - Examples present in documentation          (15 points)

OPTIONS
    -h, --help      Show this help message and exit
    -q, --quiet     Only output the final score (no details)
    --json          Output results as JSON
    --version       Show version and exit

EXAMPLES
    score-docs.sh ./my-project
        Full documentation audit with suggestions.

    score-docs.sh -q ./skills/auth
        Just the score number, useful for scripting.

EXIT STATUS
    0   Score ≥ 80 (good documentation)
    1   Score 50-79 (needs improvement)
    2   Score < 50 (poor documentation)
EOF
}

# --- Argument Parsing ---
QUIET=0
JSON=0
TARGET=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)    show_help; exit 0 ;;
        --version)    echo "score-docs.sh v${VERSION}"; exit 0 ;;
        -q|--quiet)   QUIET=1; shift ;;
        --json)       JSON=1; shift ;;
        -*)           echo "Error: Unknown option '$1'." >&2; exit 1 ;;
        *)            TARGET="$1"; shift ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    echo "Error: <path> is required." >&2
    exit 1
fi

if [[ ! -d "$TARGET" ]]; then
    echo "Error: '$TARGET' is not a directory." >&2
    exit 1
fi

TARGET="$(cd "$TARGET" && pwd)"

# --- Use temp files for details/suggestions (avoids subshell array issues) ---
_DETAILS=$(mktemp)
_SUGGESTIONS=$(mktemp)
trap 'rm -f "$_DETAILS" "$_SUGGESTIONS"' EXIT

add_detail() { echo "$1" >> "$_DETAILS"; }
add_suggest() { echo "$1" >> "$_SUGGESTIONS"; }

TOTAL=0

# =============================================================================
# Check 1: README/SKILL.md exists (15 points)
# =============================================================================
s=0
if [[ -f "$TARGET/README.md" ]] || [[ -f "$TARGET/SKILL.md" ]]; then
    f="$TARGET/README.md"; [[ -f "$f" ]] || f="$TARGET/SKILL.md"
    lines=$(wc -l < "$f")
    if [[ "$lines" -ge 10 ]]; then
        add_detail "README/SKILL.md: EXISTS, ${lines} lines [15/15]"; s=15
    else
        add_detail "README/SKILL.md: EXISTS but short (${lines} lines) [8/15]"
        add_suggest "Expand your README/SKILL.md — it's only $lines lines"; s=8
    fi
else
    add_detail "README/SKILL.md: MISSING [0/15]"
    add_suggest "Add a README.md or SKILL.md — this is the most important doc"; s=0
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 2: README quality (10 points)
# =============================================================================
s=0
f=""; [[ -f "$TARGET/README.md" ]] && f="$TARGET/README.md"; [[ -f "$TARGET/SKILL.md" ]] && f="$TARGET/SKILL.md"
if [[ -n "$f" ]]; then
    grep -q '^[^#].\{20,\}' "$f" && s=$((s + 4))
    grep -q '```' "$f" && s=$((s + 3))
    sections=$(grep -c '^##' "$f" 2>/dev/null || echo 0)
    [[ "$sections" -ge 3 ]] && s=$((s + 3))
    add_detail "README quality: ${s}/10"
    [[ "$s" -lt 7 ]] && add_suggest "Improve README: add description, code examples, and multiple sections"
else
    add_detail "README quality: N/A [0/10]"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 3: Inline comment ratio (20 points)
# =============================================================================
total_files=0; commented_files=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    total_files=$((total_files + 1))
    ext="${file##*.}"
    tl=$(wc -l < "$file" 2>/dev/null || echo 0)
    [[ "$tl" -eq 0 ]] && continue
    case "$ext" in
        sh|bash|py|rb) cl=$(grep -c '^\s*#' "$file" 2>/dev/null || echo 0) ;;
        js|ts|tsx|jsx|go|rs|java) cl=$(grep -c '^\s*\(//\|/\*\|\*\)' "$file" 2>/dev/null || echo 0) ;;
        *) cl=0 ;;
    esac
    [[ $((cl * 100 / tl)) -ge 5 ]] && commented_files=$((commented_files + 1))
done < <(find "$TARGET" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.ts" \
    -o -name "*.go" -o -name "*.rs" -o -name "*.rb" -o -name "*.java" \) 2>/dev/null)
if [[ "$total_files" -eq 0 ]]; then
    add_detail "Inline comments: N/A (no source files) [20/20]"; s=20
else
    pct=$((commented_files * 100 / total_files))
    s=$((pct * 20 / 100))
    add_detail "Inline comments: ${commented_files}/${total_files} files ≥5% comments (${pct}%) [${s}/20]"
    [[ "$s" -lt 15 ]] && add_suggest "Add inline comments to source files — explain WHY, not just WHAT"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 4: Docstrings/JSDoc (20 points)
# =============================================================================
total_funcs=0; documented_funcs=0
# Python
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    fc=$(grep -c '^\s*def ' "$file" 2>/dev/null || echo 0)
    dc=$(grep -c '"""' "$file" 2>/dev/null || echo 0)
    total_funcs=$((total_funcs + fc))
    documented_funcs=$((documented_funcs + dc / 2))
done < <(find "$TARGET" -type f -name "*.py" 2>/dev/null)
# JS/TS
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    fc=$(grep -c '^\s*\(export \)\?\(async \)\?function' "$file" 2>/dev/null || echo 0)
    dc=$(grep -c '/\*\*' "$file" 2>/dev/null || echo 0)
    total_funcs=$((total_funcs + fc))
    documented_funcs=$((documented_funcs + dc))
done < <(find "$TARGET" -type f \( -name "*.js" -o -name "*.ts" -o -name "*.tsx" \) 2>/dev/null)
# Shell
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    fc=$(grep -c '^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*()\s*{' "$file" 2>/dev/null || echo 0)
    dc=0
    while IFS= read -r ln; do
        [[ -z "$ln" ]] && continue
        prev=$((ln - 1)); [[ "$prev" -lt 1 ]] && continue
        prev_line=$(sed -n "${prev}p" "$file")
        [[ "$prev_line" =~ ^[[:space:]]*# ]] && dc=$((dc + 1))
    done < <(grep -n '^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*()\s*{' "$file" 2>/dev/null | cut -d: -f1)
    total_funcs=$((total_funcs + fc))
    documented_funcs=$((documented_funcs + dc))
done < <(find "$TARGET" -type f -name "*.sh" 2>/dev/null)
if [[ "$total_funcs" -eq 0 ]]; then
    add_detail "Docstrings/JSDoc: N/A (no functions) [20/20]"; s=20
else
    [[ "$documented_funcs" -gt "$total_funcs" ]] && documented_funcs=$total_funcs
    pct=$((documented_funcs * 100 / total_funcs))
    s=$((pct * 20 / 100))
    add_detail "Docstrings/JSDoc: ${documented_funcs}/${total_funcs} documented (${pct}%) [${s}/20]"
    [[ "$s" -lt 15 ]] && add_suggest "Add docstrings/JSDoc to functions"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 5: --help support in shell scripts (15 points)
# =============================================================================
total_scripts=0; with_help=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    total_scripts=$((total_scripts + 1))
    grep -q '\-\-help' "$file" 2>/dev/null && with_help=$((with_help + 1))
done < <(find "$TARGET" -type f -name "*.sh" 2>/dev/null)
if [[ "$total_scripts" -eq 0 ]]; then
    add_detail "--help support: N/A (no scripts) [15/15]"; s=15
else
    pct=$((with_help * 100 / total_scripts))
    s=$((pct * 15 / 100))
    add_detail "--help support: ${with_help}/${total_scripts} scripts (${pct}%) [${s}/15]"
    [[ "$s" -lt 12 ]] && add_suggest "Add --help to shell scripts — run: inject-help.sh $TARGET"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 6: CHANGELOG (5 points)
# =============================================================================
if [[ -f "$TARGET/CHANGELOG.md" ]]; then
    add_detail "CHANGELOG.md: EXISTS [5/5]"; s=5
else
    add_detail "CHANGELOG.md: MISSING [0/5]"
    add_suggest "Add a CHANGELOG.md to track version history"; s=0
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 7: Examples in docs (15 points)
# =============================================================================
has_examples=0; total_docs=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    total_docs=$((total_docs + 1))
    grep -q '```' "$file" 2>/dev/null && has_examples=$((has_examples + 1))
done < <(find "$TARGET" -type f -name "*.md" 2>/dev/null)
if [[ "$total_docs" -eq 0 ]]; then
    add_detail "Examples: N/A (no .md files) [0/15]"
    add_suggest "Add Markdown docs with code examples"; s=0
else
    pct=$((has_examples * 100 / total_docs))
    s=$((pct * 15 / 100))
    add_detail "Examples: ${has_examples}/${total_docs} docs have examples (${pct}%) [${s}/15]"
    [[ "$s" -lt 10 ]] && add_suggest "Add code examples to Markdown docs"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Output
# =============================================================================

project_name=$(basename "$TARGET")

if [[ "$JSON" -eq 1 ]]; then
    echo "{"
    echo "  \"project\": \"$project_name\","
    echo "  \"score\": $TOTAL,"
    echo "  \"details\": ["
    first=1
    while IFS= read -r line; do
        [[ "$first" -eq 0 ]] && echo ","
        printf "    \"%s\"" "$line"
        first=0
    done < "$_DETAILS"
    echo ""
    echo "  ],"
    echo "  \"suggestions\": ["
    first=1
    while IFS= read -r line; do
        [[ "$first" -eq 0 ]] && echo ","
        printf "    \"%s\"" "$line"
        first=0
    done < "$_SUGGESTIONS"
    echo ""
    echo "  ]"
    echo "}"
elif [[ "$QUIET" -eq 1 ]]; then
    echo "$TOTAL"
else
    echo "============================================="
    echo "  Documentation Quality Report: $project_name"
    echo "============================================="
    echo ""
    echo "Score: ${TOTAL}/100"
    echo ""
    echo "--- Breakdown ---"
    while IFS= read -r line; do
        echo "  $line"
    done < "$_DETAILS"
    echo ""
    if [[ -s "$_SUGGESTIONS" ]]; then
        echo "--- Suggestions ---"
        while IFS= read -r line; do
            echo "  → $line"
        done < "$_SUGGESTIONS"
    else
        echo "No suggestions — documentation looks great!"
    fi
    echo ""
    if [[ "$TOTAL" -ge 80 ]]; then
        echo "Rating: ★★★★★ EXCELLENT"
    elif [[ "$TOTAL" -ge 60 ]]; then
        echo "Rating: ★★★☆☆ GOOD"
    elif [[ "$TOTAL" -ge 40 ]]; then
        echo "Rating: ★★☆☆☆ FAIR"
    else
        echo "Rating: ★☆☆☆☆ POOR"
    fi
fi

# Exit code based on score
if [[ "$TOTAL" -ge 80 ]]; then exit 0
elif [[ "$TOTAL" -ge 50 ]]; then exit 1
else exit 2; fi
