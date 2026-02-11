#!/usr/bin/env bash
# =============================================================================
# score-docs.sh — Documentation quality auditor v2.0 (Gold Standard)
#
# Strict scoring with Diátaxis structure checks, template detection,
# CONTRIBUTING.md and CHANGELOG.md requirements.
#
# Total: 100 points + penalties for template leftovers.
# Exit codes: 0 (≥80), 1 (50-79), 2 (<50).
# =============================================================================

set -euo pipefail

VERSION="2.0.0"

show_help() {
    cat <<'EOF'
NAME
    score-docs.sh — documentation quality auditor (Gold Standard v2.0)

SYNOPSIS
    score-docs.sh [OPTIONS] <path>

DESCRIPTION
    Scans a project or skill directory and produces a documentation quality
    score from 0 to 100, with penalties and improvement suggestions.

    v2.0 Changes:
      - CONTRIBUTING.md now required (10 pts)
      - CHANGELOG.md now required (10 pts)
      - Diátaxis docs/ structure checked (10 pts)
      - README template detection PENALTY (-10 pts)
      - Stricter ratings (EXCELLENT ≥85)

    Scoring breakdown (100 points):
      README/SKILL.md exists           10 pts
      README quality                   10 pts
      CONTRIBUTING.md exists           10 pts
      CHANGELOG.md exists              10 pts
      Diátaxis docs/ structure         10 pts
      Inline comment ratio             15 pts
      Docstrings/JSDoc coverage        15 pts
      Shell --help support             10 pts
      Examples in docs                 10 pts
      README template penalty          -10 pts (if applicable)

OPTIONS
    -h, --help      Show this help message and exit
    -q, --quiet     Only output the final score
    --json          Output results as JSON
    --version       Show version and exit

EXAMPLES
    score-docs.sh ./my-project
        Full documentation audit with suggestions.

    score-docs.sh -q ./skills/auth
        Just the score number.

    score-docs.sh --json ./my-project
        Machine-readable JSON output.

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

# --- Temp files for results ---
_DETAILS=$(mktemp)
_SUGGESTIONS=$(mktemp)
trap 'rm -f "$_DETAILS" "$_SUGGESTIONS"' EXIT

add_detail() { echo "$1" >> "$_DETAILS"; }
add_suggest() { echo "$1" >> "$_SUGGESTIONS"; }

# Helper: safe grep -c that always returns a clean integer
grepcount() {
    local result
    result=$(grep -c "$@" 2>/dev/null || true)
    result="${result%%$'\n'*}"
    result="${result// /}"
    [[ -z "$result" ]] && result=0
    echo "$result"
}

# Case-insensitive variant
grepcounti() {
    local result
    result=$(grep -ci "$@" 2>/dev/null || true)
    result="${result%%$'\n'*}"
    result="${result// /}"
    [[ -z "$result" ]] && result=0
    echo "$result"
}

TOTAL=0
PENALTY=0

# =============================================================================
# Check 1: README/SKILL.md exists (10 points)
# =============================================================================
s=0
if [[ -f "$TARGET/README.md" ]] || [[ -f "$TARGET/SKILL.md" ]]; then
    f="$TARGET/README.md"; [[ -f "$f" ]] || f="$TARGET/SKILL.md"
    lines=$(wc -l < "$f" | tr -d " ")
    if [[ "$lines" -ge 10 ]]; then
        s=10
        add_detail "README/SKILL.md: EXISTS, ${lines} lines [${s}/10]"
    else
        s=5
        add_detail "README/SKILL.md: EXISTS but short (${lines} lines) [${s}/10]"
        add_suggest "Expand README/SKILL.md — it's only $lines lines"
    fi
else
    add_detail "README/SKILL.md: MISSING [0/10]"
    add_suggest "Add a README.md — this is the most important documentation file"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 2: README quality (10 points)
# =============================================================================
s=0
f=""
[[ -f "$TARGET/README.md" ]] && f="$TARGET/README.md"
[[ -z "$f" ]] && [[ -f "$TARGET/SKILL.md" ]] && f="$TARGET/SKILL.md"
if [[ -n "$f" ]]; then
    # Has meaningful description (non-header text ≥20 chars)
    grep -q '^[^#].\{20,\}' "$f" && s=$((s + 3))
    # Has code examples
    grep -q '```' "$f" && s=$((s + 3))
    # Has multiple sections
    sections=$(grepcount '^##' "$f")
    [[ "$sections" -ge 3 ]] && s=$((s + 2))
    # Has install or usage section
    grep -qi '\(install\|usage\|quick start\|getting started\)' "$f" && s=$((s + 2))
    add_detail "README quality: ${s}/10"
    [[ "$s" -lt 7 ]] && add_suggest "Improve README: add description, code examples, usage section, and ≥3 sections"
else
    add_detail "README quality: N/A [0/10]"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 3: README template detection (PENALTY: -10)
# =============================================================================
if [[ -n "$f" ]]; then
    is_template=0
    # Check for common template placeholder patterns
    grep -q '\[Project Name\]' "$f" 2>/dev/null && is_template=1
    grep -q '\[project-name\]' "$f" 2>/dev/null && is_template=1
    grep -q '\[TODO' "$f" 2>/dev/null && is_template=1
    # Count TODO occurrences — more than 3 means it's basically unedited
    todo_count=$(grepcounti 'TODO' "$f")
    [[ "$todo_count" -ge 4 ]] && is_template=1

    if [[ "$is_template" -eq 1 ]]; then
        PENALTY=$((PENALTY + 10))
        add_detail "README template check: PENALTY -10 (contains unedited template text)"
        add_suggest "Edit your README — replace all [Project Name], [TODO], and placeholder text"
    else
        add_detail "README template check: PASS (no template placeholders detected)"
    fi
fi

# =============================================================================
# Check 4: CONTRIBUTING.md exists (10 points)
# =============================================================================
s=0
if [[ -f "$TARGET/CONTRIBUTING.md" ]]; then
    lines=$(wc -l < "$TARGET/CONTRIBUTING.md" | tr -d " ")
    if [[ "$lines" -ge 10 ]]; then
        s=10
        add_detail "CONTRIBUTING.md: EXISTS, ${lines} lines [10/10]"
    else
        s=5
        add_detail "CONTRIBUTING.md: EXISTS but short (${lines} lines) [5/10]"
        add_suggest "Expand CONTRIBUTING.md with setup instructions and PR workflow"
    fi
else
    add_detail "CONTRIBUTING.md: MISSING [0/10]"
    add_suggest "Add CONTRIBUTING.md — run: document.sh $TARGET scaffold"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 5: CHANGELOG.md exists (10 points)
# =============================================================================
s=0
if [[ -f "$TARGET/CHANGELOG.md" ]]; then
    lines=$(wc -l < "$TARGET/CHANGELOG.md" | tr -d " ")
    if [[ "$lines" -ge 5 ]]; then
        s=10
        add_detail "CHANGELOG.md: EXISTS, ${lines} lines [10/10]"
    else
        s=5
        add_detail "CHANGELOG.md: EXISTS but minimal (${lines} lines) [5/10]"
    fi
else
    add_detail "CHANGELOG.md: MISSING [0/10]"
    add_suggest "Add CHANGELOG.md — run: document.sh $TARGET scaffold"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 6: Diátaxis docs/ structure (10 points)
# =============================================================================
s=0
diataxis_dirs=0
for dir in tutorials how-to reference explanations; do
    [[ -d "$TARGET/docs/$dir" ]] && diataxis_dirs=$((diataxis_dirs + 1))
done
if [[ "$diataxis_dirs" -ge 4 ]]; then
    s=10
    add_detail "Diátaxis docs/ structure: COMPLETE (${diataxis_dirs}/4 dirs) [10/10]"
elif [[ "$diataxis_dirs" -ge 2 ]]; then
    s=5
    add_detail "Diátaxis docs/ structure: PARTIAL (${diataxis_dirs}/4 dirs) [5/10]"
    add_suggest "Complete the Diátaxis structure: docs/{tutorials,how-to,reference,explanations}"
elif [[ -d "$TARGET/docs" ]]; then
    s=2
    add_detail "Diátaxis docs/ structure: EXISTS but no Diátaxis dirs (${diataxis_dirs}/4) [2/10]"
    add_suggest "Add Diátaxis subdirectories: docs/{tutorials,how-to,reference,explanations}"
else
    add_detail "Diátaxis docs/ structure: MISSING [0/10]"
    add_suggest "Create docs/ with Diátaxis structure — run: document.sh $TARGET scaffold"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 7: Inline comment ratio (15 points)
# =============================================================================
total_files=0; commented_files=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    total_files=$((total_files + 1))
    ext="${file##*.}"
    tl=$(wc -l < "$file" 2>/dev/null | tr -d ' ' || echo 0)
    [[ -z "$tl" || "$tl" -eq 0 ]] && continue
    case "$ext" in
        sh|bash|py|rb) cl=$(grepcount '^\s*#' "$file") ;;
        js|ts|tsx|jsx|go|rs|java) cl=$(grepcount '^\s*\(//\|/\*\|\*\)' "$file") ;;
        *) cl=0 ;;
    esac
    [[ $((cl * 100 / tl)) -ge 5 ]] && commented_files=$((commented_files + 1))
done < <(find "$TARGET" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.ts" \
    -o -name "*.go" -o -name "*.rs" -o -name "*.rb" -o -name "*.java" \) \
    -not -path '*/node_modules/*' -not -path '*/__pycache__/*' -not -path '*/.git/*' 2>/dev/null)
if [[ "$total_files" -eq 0 ]]; then
    add_detail "Inline comments: N/A (no source files) [15/15]"; s=15
else
    pct=$((commented_files * 100 / total_files))
    s=$((pct * 15 / 100))
    add_detail "Inline comments: ${commented_files}/${total_files} files ≥5% comments (${pct}%) [${s}/15]"
    [[ "$s" -lt 10 ]] && add_suggest "Add inline comments to source files — explain WHY, not WHAT"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 8: Docstrings/JSDoc (15 points)
# =============================================================================
total_funcs=0; documented_funcs=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    fc=$(grepcount '^\s*def ' "$file")
    dc=$(grepcount '"""' "$file")
    total_funcs=$((total_funcs + fc))
    documented_funcs=$((documented_funcs + dc / 2))
done < <(find "$TARGET" -type f -name "*.py" -not -path '*/node_modules/*' -not -path '*/__pycache__/*' 2>/dev/null)
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    fc=$(grepcount '^\s*\(export \)\?\(async \)\?function' "$file")
    dc=$(grepcount '/\*\*' "$file")
    total_funcs=$((total_funcs + fc))
    documented_funcs=$((documented_funcs + dc))
done < <(find "$TARGET" -type f \( -name "*.js" -o -name "*.ts" -o -name "*.tsx" \) \
    -not -path '*/node_modules/*' 2>/dev/null)
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    fc=$(grepcount '^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*()\s*{' "$file")
    dc=0
    while IFS= read -r ln; do
        [[ -z "$ln" ]] && continue
        ln=$(echo "$ln" | tr -d ' ')
        prev=$((ln - 1)); [[ "$prev" -lt 1 ]] && continue
        prev_line=$(sed -n "${prev}p" "$file")
        [[ "$prev_line" =~ ^[[:space:]]*# ]] && dc=$((dc + 1))
    done < <(grep -n '^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*()\s*{' "$file" 2>/dev/null | cut -d: -f1)
    total_funcs=$((total_funcs + fc))
    documented_funcs=$((documented_funcs + dc))
done < <(find "$TARGET" -type f -name "*.sh" -not -path '*/.git/*' 2>/dev/null)
if [[ "$total_funcs" -eq 0 ]]; then
    add_detail "Docstrings/JSDoc: N/A (no functions) [15/15]"; s=15
else
    [[ "$documented_funcs" -gt "$total_funcs" ]] && documented_funcs=$total_funcs
    pct=$((documented_funcs * 100 / total_funcs))
    s=$((pct * 15 / 100))
    add_detail "Docstrings/JSDoc: ${documented_funcs}/${total_funcs} documented (${pct}%) [${s}/15]"
    [[ "$s" -lt 10 ]] && add_suggest "Add docstrings/JSDoc to functions"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 9: --help support in shell scripts (10 points)
# =============================================================================
total_scripts=0; with_help=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    total_scripts=$((total_scripts + 1))
    grep -q '\-\-help' "$file" 2>/dev/null && with_help=$((with_help + 1))
done < <(find "$TARGET" -type f -name "*.sh" -not -path '*/.git/*' 2>/dev/null)
if [[ "$total_scripts" -eq 0 ]]; then
    add_detail "--help support: N/A (no scripts) [10/10]"; s=10
else
    pct=$((with_help * 100 / total_scripts))
    s=$((pct * 10 / 100))
    add_detail "--help support: ${with_help}/${total_scripts} scripts (${pct}%) [${s}/10]"
    [[ "$s" -lt 8 ]] && add_suggest "Add --help to shell scripts — run: inject-help.sh $TARGET"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Check 10: Examples in docs (10 points)
# =============================================================================
has_examples=0; total_docs=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    total_docs=$((total_docs + 1))
    grep -q '```' "$file" 2>/dev/null && has_examples=$((has_examples + 1))
done < <(find "$TARGET" -type f -name "*.md" -not -path '*/.git/*' 2>/dev/null)
if [[ "$total_docs" -eq 0 ]]; then
    add_detail "Examples: N/A (no .md files) [0/10]"
    add_suggest "Add Markdown documentation with code examples"; s=0
else
    pct=$((has_examples * 100 / total_docs))
    s=$((pct * 10 / 100))
    add_detail "Examples: ${has_examples}/${total_docs} docs have code examples (${pct}%) [${s}/10]"
    [[ "$s" -lt 7 ]] && add_suggest "Add code examples to Markdown documentation"
fi
TOTAL=$((TOTAL + s))

# =============================================================================
# Apply penalty
# =============================================================================
FINAL=$((TOTAL - PENALTY))
[[ "$FINAL" -lt 0 ]] && FINAL=0

# =============================================================================
# Output
# =============================================================================

project_name=$(basename "$TARGET")

if [[ "$JSON" -eq 1 ]]; then
    echo "{"
    echo "  \"project\": \"$project_name\","
    echo "  \"score\": $FINAL,"
    echo "  \"raw_score\": $TOTAL,"
    echo "  \"penalty\": $PENALTY,"
    echo "  \"details\": ["
    first=1
    while IFS= read -r line; do
        [[ "$first" -eq 0 ]] && echo ","
        printf "    \"%s\"" "$(echo "$line" | sed 's/"/\\"/g')"
        first=0
    done < "$_DETAILS"
    echo ""
    echo "  ],"
    echo "  \"suggestions\": ["
    first=1
    while IFS= read -r line; do
        [[ "$first" -eq 0 ]] && echo ","
        printf "    \"%s\"" "$(echo "$line" | sed 's/"/\\"/g')"
        first=0
    done < "$_SUGGESTIONS"
    echo ""
    echo "  ]"
    echo "}"
elif [[ "$QUIET" -eq 1 ]]; then
    echo "$FINAL"
else
    echo "╔═══════════════════════════════════════════════╗"
    echo "║  Documentation Quality Report (v2.0)         ║"
    echo "║  Project: $project_name"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    if [[ "$PENALTY" -gt 0 ]]; then
        echo "  Score: ${FINAL}/100 (${TOTAL} raw - ${PENALTY} penalty)"
    else
        echo "  Score: ${FINAL}/100"
    fi
    echo ""
    echo "── Breakdown ──"
    while IFS= read -r line; do
        echo "  $line"
    done < "$_DETAILS"
    echo ""
    if [[ -s "$_SUGGESTIONS" ]]; then
        echo "── Suggestions ──"
        while IFS= read -r line; do
            echo "  → $line"
        done < "$_SUGGESTIONS"
    else
        echo "  ✓ No suggestions — documentation meets the Gold Standard!"
    fi
    echo ""
    if [[ "$FINAL" -ge 85 ]]; then
        echo "  Rating: ★★★★★ EXCELLENT"
    elif [[ "$FINAL" -ge 70 ]]; then
        echo "  Rating: ★★★★☆ GOOD"
    elif [[ "$FINAL" -ge 55 ]]; then
        echo "  Rating: ★★★☆☆ FAIR"
    elif [[ "$FINAL" -ge 40 ]]; then
        echo "  Rating: ★★☆☆☆ POOR"
    else
        echo "  Rating: ★☆☆☆☆ FAILING"
    fi
fi

# Exit code based on score
if [[ "$FINAL" -ge 80 ]]; then exit 0
elif [[ "$FINAL" -ge 50 ]]; then exit 1
else exit 2; fi
