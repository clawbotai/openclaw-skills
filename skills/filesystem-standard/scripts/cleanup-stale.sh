#!/usr/bin/env bash
set -euo pipefail

# cleanup-stale.sh — Remove stale backups, old logs, orphaned sessions
# Usage: cleanup-stale.sh [--dry-run] [--help]

DRY_RUN=false
HOME_DIR="${HOME:-/Users/clawai}"
OPENCLAW="${HOME_DIR}/.openclaw"
REMOVED=0


usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Clean up stale files in the OpenClaw filesystem.

Options:
  --dry-run   Show what would be removed without removing
  --help      Show this help

Targets:
  - Config backups: keep max 1 .bak file
  - System logs: remove files older than 7 days
  - Subagent sessions: remove sessions older than 24h
  - Cron run logs: remove runs older than 7 days
  - Stale home log: ~/openclaw.log
EOF
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --help) usage ;;
        *) echo "Unknown option: $arg"; usage ;;
    esac
done


remove_file() {
    local path="$1" reason="$2"
    REMOVED=$((REMOVED + 1))
    if $DRY_RUN; then
        echo "  📋 Would remove: $path ($reason)"
    else
        rm -f "$path"
        echo "  🗑️  Removed: $path ($reason)"
    fi
}


remove_dir() {
    local path="$1" reason="$2"
    REMOVED=$((REMOVED + 1))
    if $DRY_RUN; then
        echo "  📋 Would remove: $path/ ($reason)"
    else
        rm -rf "$path"
        echo "  🗑️  Removed: $path/ ($reason)"
    fi
}

echo "Mode: $($DRY_RUN && echo "dry-run" || echo "live")"
echo ""

# ── Config Backups ──
echo "━━━ Config Backups ━━━"
bak_files=$(ls -t "$OPENCLAW"/openclaw.json.bak* 2>/dev/null || true)
bak_count=$(echo "$bak_files" | grep -c . 2>/dev/null || echo 0)
if [ "$bak_count" -gt 1 ]; then
    echo "$bak_files" | tail -n +2 | while read -r f; do
        [ -n "$f" ] && remove_file "$f" "excess backup"
    done
else
    echo "  ✅ Backups OK ($bak_count file(s))"
fi

# ── Old Logs ──
echo ""
echo "━━━ Old Logs ━━━"
if [ -d "$OPENCLAW/logs" ]; then
    find "$OPENCLAW/logs" -type f -mtime +7 2>/dev/null | while read -r f; do
        remove_file "$f" "older than 7 days"
    done
    remaining=$(find "$OPENCLAW/logs" -type f -mtime +7 2>/dev/null | wc -l | tr -d ' ')
    [ "$remaining" -eq 0 ] && echo "  ✅ All logs within retention"
fi

# Stale home log
if [ -f "$HOME_DIR/openclaw.log" ]; then
    remove_file "$HOME_DIR/openclaw.log" "stale log in home root"
else
    echo "  ✅ No stale openclaw.log"
fi

# ── Subagent Sessions ──
echo ""
echo "━━━ Subagent Sessions ━━━"
if [ -d "$OPENCLAW/subagents" ]; then
    old_sessions=$(find "$OPENCLAW/subagents" -maxdepth 1 -type d -mtime +1 2>/dev/null | grep -v "^${OPENCLAW}/subagents$" || true)
    if [ -n "$old_sessions" ]; then
        echo "$old_sessions" | while read -r d; do
            [ -n "$d" ] && remove_dir "$d" "session older than 24h"
        done
    else
        echo "  ✅ No stale sessions"
    fi
fi

# ── Cron Runs ──
echo ""
echo "━━━ Cron Run History ━━━"
if [ -d "$OPENCLAW/cron/runs" ]; then
    find "$OPENCLAW/cron/runs" -type f -mtime +7 2>/dev/null | while read -r f; do
        remove_file "$f" "cron run older than 7 days"
    done
fi
echo "  ✅ Cron runs checked"

# ── Results ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $REMOVED -eq 0 ]; then
    echo "  ✅ Nothing to clean up"
else
    echo "  $REMOVED item(s) $($DRY_RUN && echo "would be removed" || echo "removed")"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
