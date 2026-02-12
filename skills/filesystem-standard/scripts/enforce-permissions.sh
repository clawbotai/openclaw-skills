#!/usr/bin/env bash
set -euo pipefail

# enforce-permissions.sh — Set correct permissions on all OpenClaw directories
# Usage: enforce-permissions.sh [--dry-run | --apply] [--help]

MODE="dry-run"
HOME_DIR="${HOME:-/Users/clawai}"
WORKSPACE="${HOME_DIR}/openclaw/workspace"
OPENCLAW="${HOME_DIR}/.openclaw"

# usage — handles usage operation
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Set correct permissions on all OpenClaw directories and files.

Options:
  --dry-run   Show what would change (default)
  --apply     Actually apply permission changes
  --help      Show this help

Permission Standards:
  credentials/      → 700 (dir), 600 (files)
  openclaw.json     → 600
  *.sh, *.py        → 755
  All other files   → 644
  All directories   → 755
EOF
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --dry-run) MODE="dry-run" ;;
        --apply) MODE="apply" ;;
        --help) usage ;;
        *) echo "Unknown option: $arg"; usage ;;
    esac
done

CHANGES=0

# set_perm — handles set perm operation
set_perm() {
    local path="$1" perm="$2"
    [ -e "$path" ] || return 0
    actual=$(stat -f "%Lp" "$path" 2>/dev/null || stat -c "%a" "$path" 2>/dev/null)
    if [ "$actual" != "$perm" ]; then
        CHANGES=$((CHANGES + 1))
        if [ "$MODE" = "apply" ]; then
            chmod "$perm" "$path"
            echo "  🔧 $path: $actual → $perm"
        else
            echo "  📋 $path: $actual → $perm (dry-run)"
        fi
    fi
}

echo "Mode: $MODE"
echo ""

# Credentials
echo "━━━ Credentials ━━━"
set_perm "$OPENCLAW/credentials" "700"
if [ -d "$OPENCLAW/credentials" ]; then
    for f in "$OPENCLAW/credentials"/*; do
        [ -f "$f" ] && set_perm "$f" "600"
    done
fi

# Sensitive configs
echo "━━━ Sensitive Configs ━━━"
set_perm "$OPENCLAW/openclaw.json" "600"

# Directories → 755
echo "━━━ Directories ━━━"
for dir in "$OPENCLAW" "$OPENCLAW/agents" "$OPENCLAW/cron" "$OPENCLAW/devices" \
           "$OPENCLAW/logs" "$OPENCLAW/sandbox" "$OPENCLAW/subagents" \
           "$WORKSPACE" "$WORKSPACE/memory" "$WORKSPACE/skills"; do
    set_perm "$dir" "755"
done

# Scripts → 755
echo "━━━ Scripts ━━━"
find "$WORKSPACE/skills" -name "*.sh" -type f 2>/dev/null | while read -r f; do
    set_perm "$f" "755"
done
if [ -d "$HOME_DIR/scripts" ]; then
    find "$HOME_DIR/scripts" -name "*.sh" -type f 2>/dev/null | while read -r f; do
        set_perm "$f" "755"
    done
fi

# Workspace files → 644
echo "━━━ Workspace Files ━━━"
for f in "$WORKSPACE"/*.md "$WORKSPACE/.env" "$WORKSPACE/.gitignore"; do
    [ -f "$f" ] && set_perm "$f" "644"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $CHANGES -eq 0 ]; then
    echo "  ✅ All permissions correct"
else
    echo "  $CHANGES change(s) $([ "$MODE" = "apply" ] && echo "applied" || echo "needed (use --apply)")"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
