#!/usr/bin/env bash
# =============================================================================
# inject-help.sh — Inject --help support into shell scripts
#
# Takes a shell script (or directory of scripts) and adds a show_help()
# function plus --help/-h flag handling. Preserves existing functionality.
# If the script already has --help handling, it's skipped.
# =============================================================================

set -euo pipefail

VERSION="1.0.0"

# =============================================================================
# Help
# =============================================================================

# show_help — handles show help operation
show_help() {
    cat <<'EOF'
NAME
    inject-help.sh — add --help support to shell scripts

SYNOPSIS
    inject-help.sh [OPTIONS] <path>

DESCRIPTION
    Scans a shell script (or all .sh files in a directory, recursively) and
    injects a show_help() function with standard POSIX-style help output.
    Also adds --help and -h flag parsing near the top of the script.

    If the script already contains "--help" handling, it is skipped to avoid
    duplication. The injected help is based on the script's filename and any
    existing comments at the top of the file.

    The injected help function uses a standard format:
        NAME, SYNOPSIS, DESCRIPTION, OPTIONS, EXIT STATUS

OPTIONS
    -h, --help      Show this help message and exit
    -n, --dry-run   Show what would be changed without modifying files
    -f, --force     Inject even if --help handling already exists
    --version       Show version and exit

EXAMPLES
    inject-help.sh ./scripts/deploy.sh
        Add --help to a single script.

    inject-help.sh ./scripts/
        Add --help to all .sh files under ./scripts/ recursively.

    inject-help.sh --dry-run ./my-project/
        Preview what would be changed without modifying anything.

EXIT STATUS
    0   Success (files processed or nothing to do)
    1   Error (invalid arguments, path not found)
EOF
}

# =============================================================================
# Argument Parsing
# =============================================================================

DRY_RUN=0
FORCE=0
TARGET=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)    show_help; exit 0 ;;
        --version)    echo "inject-help.sh v${VERSION}"; exit 0 ;;
        -n|--dry-run) DRY_RUN=1; shift ;;
        -f|--force)   FORCE=1; shift ;;
        -*)           echo "Error: Unknown option '$1'. Use --help for usage." >&2; exit 1 ;;
        *)            TARGET="$1"; shift ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    echo "Error: <path> is required." >&2
    echo "Usage: inject-help.sh [OPTIONS] <path>" >&2
    exit 1
fi

if [[ ! -e "$TARGET" ]]; then
    echo "Error: '$TARGET' does not exist." >&2
    exit 1
fi

# =============================================================================
# Core: Inject help into a single script
# =============================================================================

# inject_help_into_file — handles inject help into file operation
inject_help_into_file() {
    local file="$1"
    local basename_script
    basename_script=$(basename "$file" .sh)

    # Skip if already has --help handling (unless --force)
    if [[ "$FORCE" -eq 0 ]] && grep -q '\-\-help' "$file" 2>/dev/null; then
        echo "  SKIP (already has --help): $file"
        return 0
    fi

    # Extract description from top comments (lines 2-10 starting with #)
    local description=""
    description=$(sed -n '2,10s/^#\s*//p' "$file" | head -3 | tr '\n' ' ' | sed 's/\s*$//')
    [[ -z "$description" ]] && description="No description available. Edit show_help() to add one."

    # Build the help block
    local help_block
    help_block=$(cat <<HELPEOF

# --- Auto-injected by master-docs/inject-help.sh ---
show_help() {
    cat <<'ENDHELP'
NAME
    ${basename_script} — ${description}

SYNOPSIS
    ${basename_script}.sh [OPTIONS]

DESCRIPTION
    ${description}

OPTIONS
    -h, --help    Show this help message and exit

EXIT STATUS
    0   Success
    1   Error
ENDHELP
}

# Parse --help / -h flags
for arg in "\$@"; do
    case "\$arg" in
        -h|--help) show_help; exit 0 ;;
    esac
done
# --- End auto-injected help ---
HELPEOF
)

    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "  WOULD INJECT: $file"
        return 0
    fi

    # Inject after the shebang line (or after initial comment block)
    # Find the line number of the first non-comment, non-empty, non-shebang line
    local inject_after=1
    local line_num=0
    while IFS= read -r line; do
        line_num=$((line_num + 1))
        # Skip shebang, comments, empty lines, and set commands at the top
        if [[ "$line" =~ ^#.* ]] || [[ "$line" =~ ^$ ]] || [[ "$line" =~ ^set\ .* ]]; then
            inject_after=$line_num
        else
            break
        fi
    done < "$file"

    # Split the file and insert the help block
    local tmp
    tmp=$(mktemp)
    head -n "$inject_after" "$file" > "$tmp"
    echo "$help_block" >> "$tmp"
    tail -n +"$((inject_after + 1))" "$file" >> "$tmp"
    mv "$tmp" "$file"
    chmod +x "$file"

    echo "  INJECTED: $file"
}

# =============================================================================
# Process target (file or directory)
# =============================================================================

processed=0

if [[ -f "$TARGET" ]]; then
    # Single file
    echo "Processing: $TARGET"
    inject_help_into_file "$TARGET"
    processed=1
elif [[ -d "$TARGET" ]]; then
    # Directory — find all .sh files recursively
    echo "Scanning for .sh files in: $TARGET"
    echo ""
    while IFS= read -r file; do
        inject_help_into_file "$file"
        processed=$((processed + 1))
    done < <(find "$TARGET" -type f -name "*.sh" | sort)
fi

echo ""
echo "Done. Processed $processed file(s)."
