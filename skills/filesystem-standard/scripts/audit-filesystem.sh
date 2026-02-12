#!/usr/bin/env bash
set -euo pipefail

# audit-filesystem.sh — Audit OpenClaw filesystem against the standard
# Usage: audit-filesystem.sh [--fix] [--quiet] [--help]

SCORE=0
TOTAL=0
ISSUES=()
FIX_MODE=false
QUIET=false
HOME_DIR="${HOME:-/Users/clawai}"
WORKSPACE="${HOME_DIR}/openclaw/workspace"
OPENCLAW="${HOME_DIR}/.openclaw"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Audit the OpenClaw filesystem against the filesystem-standard.

Options:
  --fix       Auto-remediate safe issues (permissions, stale backups)
  --quiet     Only show issues and score (no passing checks)
  --help      Show this help

Checks:
  - Directory structure existence
  - Permission standards (credentials, configs, scripts)
  - Stale files and orphaned directories
  - .gitignore presence and content
  - node_modules / build artifacts in git
  - Loose files in \$HOME
EOF
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --fix) FIX_MODE=true ;;
        --quiet) QUIET=true ;;
        --help) usage ;;
        *) echo "Unknown option: $arg"; usage ;;
    esac
done

pass() {
    TOTAL=$((TOTAL + 1))
    SCORE=$((SCORE + 1))
    $QUIET || echo "  ✅ $1"
}

fail() {
    TOTAL=$((TOTAL + 1))
    ISSUES+=("$1")
    echo "  ❌ $1"
    [ -n "${2:-}" ] && echo "     💡 $2"
}

section() {
    echo ""
    echo "━━━ $1 ━━━"
}

# ── Structure Checks ──
section "Directory Structure"

for dir in "$OPENCLAW" "$OPENCLAW/agents" "$OPENCLAW/credentials" "$OPENCLAW/cron" \
           "$OPENCLAW/devices" "$OPENCLAW/logs" "$OPENCLAW/sandbox" "$OPENCLAW/subagents" \
           "$WORKSPACE" "$WORKSPACE/memory" "$WORKSPACE/skills"; do
    if [ -d "$dir" ]; then
        pass "$(basename "$dir")/ exists"
    else
        fail "Missing: $dir" "Create with: mkdir -p $dir"
    fi
done

if [ -d "$WORKSPACE/projects" ]; then
    pass "projects/ exists"
else
    fail "Missing: $WORKSPACE/projects/" "Create with: mkdir -p $WORKSPACE/projects/"
fi

if [ -d "$HOME_DIR/scripts" ]; then
    pass "~/scripts/ exists"
else
    fail "Missing: ~/scripts/ (utility scripts directory)" "Create with: mkdir -p ~/scripts/"
fi

# ── Workspace Files ──
section "Workspace Files"

for f in AGENTS.md SOUL.md IDENTITY.md USER.md TOOLS.md HEARTBEAT.md; do
    if [ -f "$WORKSPACE/$f" ]; then
        pass "$f present"
    else
        fail "Missing: $WORKSPACE/$f"
    fi
done

if [ -f "$WORKSPACE/.gitignore" ]; then
    pass ".gitignore present"
else
    fail "Missing: $WORKSPACE/.gitignore" "Copy from skills/filesystem-standard/templates/gitignore-workspace"
    if $FIX_MODE && [ -f "$WORKSPACE/skills/filesystem-standard/templates/gitignore-workspace" ]; then
        cp "$WORKSPACE/skills/filesystem-standard/templates/gitignore-workspace" "$WORKSPACE/.gitignore"
        echo "     🔧 Fixed: created .gitignore"
    fi
fi

# ── Permissions ──
section "Permissions"

check_perm() {
    local path="$1" expected="$2" label="$3"
    if [ ! -e "$path" ]; then return; fi
    actual=$(stat -f "%Lp" "$path" 2>/dev/null || stat -c "%a" "$path" 2>/dev/null)
    TOTAL=$((TOTAL + 1))
    if [ "$actual" = "$expected" ]; then
        SCORE=$((SCORE + 1))
        $QUIET || echo "  ✅ $label: $actual"
    else
        ISSUES+=("$label: expected $expected, got $actual")
        echo "  ❌ $label: expected $expected, got $actual"
        if $FIX_MODE; then
            chmod "$expected" "$path"
            echo "     🔧 Fixed: chmod $expected $path"
        else
            echo "     💡 Fix: chmod $expected $path"
        fi
    fi
}

check_perm "$OPENCLAW/credentials" "700" "credentials/ dir"
if [ -d "$OPENCLAW/credentials" ]; then
    for f in "$OPENCLAW/credentials"/*; do
        [ -f "$f" ] && check_perm "$f" "600" "credentials/$(basename "$f")"
    done
fi
check_perm "$OPENCLAW/openclaw.json" "600" "openclaw.json"

# Check scripts have +x
if [ -d "$HOME_DIR/scripts" ]; then
    for f in "$HOME_DIR/scripts"/*.sh; do
        [ -f "$f" ] && check_perm "$f" "755" "scripts/$(basename "$f")"
    done
fi

# ── Stale Files ──
section "Stale Files & Orphans"

# Backup proliferation
bak_count=$(ls "$OPENCLAW"/openclaw.json.bak* 2>/dev/null | wc -l | tr -d ' ')
if [ "$bak_count" -gt 1 ]; then
    fail "Config backup proliferation: $bak_count .bak files (max 1)" "Run cleanup-stale.sh"
    if $FIX_MODE; then
        # Keep the newest, remove the rest
        ls -t "$OPENCLAW"/openclaw.json.bak* 2>/dev/null | tail -n +2 | xargs rm -f
        echo "     🔧 Fixed: removed excess backups"
    fi
elif [ "$bak_count" -le 1 ]; then
    pass "Config backups: $bak_count (≤1)"
fi

# Stale home files
for f in "$HOME_DIR/openclaw.log" "$HOME_DIR/Clawaibot_Pristine_State.tar.gz"; do
    if [ -f "$f" ]; then
        fail "Stale file in home: $(basename "$f")" "Remove: rm $f"
    else
        pass "No stale $(basename "$f")"
    fi
done

# Orphaned directories
for d in "$HOME_DIR/skills" "$HOME_DIR/skill-inspection" "$HOME_DIR/Clawaibot_Backup"; do
    if [ -d "$d" ]; then
        count=$(find "$d" -maxdepth 1 | wc -l | tr -d ' ')
        fail "Orphaned directory: $(basename "$d")/ ($count items)" "Review and remove if unneeded"
    else
        pass "No orphaned $(basename "$d")/"
    fi
done

# Loose scripts in home
for f in "$HOME_DIR/clean_slate.sh" "$HOME_DIR/searx.sh" "$HOME_DIR/Modelfile"; do
    if [ -f "$f" ]; then
        fail "Loose file in home: $(basename "$f")" "Move to ~/scripts/"
    else
        pass "No loose $(basename "$f")"
    fi
done

# ── Git Hygiene ──
section "Git Hygiene"

# node_modules in skills
nm_found=false
if [ -d "$WORKSPACE/skills" ]; then
    while IFS= read -r nm; do
        [ -z "$nm" ] && continue
        nm_found=true
        fail "node_modules/ found: $nm" "Add to .gitignore and git rm -r --cached"
    done < <(find "$WORKSPACE/skills" -name "node_modules" -type d 2>/dev/null)
fi
$nm_found || pass "No node_modules/ in skills"

# build artifacts in skills
ba_found=false
if [ -d "$WORKSPACE/skills" ]; then
    while IFS= read -r ba; do
        [ -z "$ba" ] && continue
        ba_found=true
        fail "Build artifact found: $ba" "Add to .gitignore"
    done < <(find "$WORKSPACE/skills" -maxdepth 3 \( -name "dist" -o -name "build" \) -type d 2>/dev/null)
fi
$ba_found || pass "No build artifacts in skills"

# ── Old Logs ──
section "Log Rotation"

if [ -d "$OPENCLAW/logs" ]; then
    old_logs=$(find "$OPENCLAW/logs" -type f -mtime +7 2>/dev/null | wc -l | tr -d ' ')
    if [ "$old_logs" -gt 0 ]; then
        fail "$old_logs log files older than 7 days" "Run cleanup-stale.sh"
        if $FIX_MODE; then
            find "$OPENCLAW/logs" -type f -mtime +7 -delete
            echo "     🔧 Fixed: removed old logs"
        fi
    else
        pass "All logs within 7-day retention"
    fi
else
    pass "No logs directory to check"
fi

# ── Cron Run Cleanup ──
if [ -d "$OPENCLAW/cron" ]; then
    old_runs=$(find "$OPENCLAW/cron" -name "*.json" -type f -mtime +7 2>/dev/null | wc -l | tr -d ' ')
    if [ "$old_runs" -gt 0 ]; then
        fail "$old_runs cron run files older than 7 days"
    else
        pass "Cron runs within retention"
    fi
fi

# ── Results ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pct=$((SCORE * 100 / (TOTAL > 0 ? TOTAL : 1)))
echo "  Score: $SCORE/$TOTAL ($pct%)"
echo "  Issues: ${#ISSUES[@]}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${#ISSUES[@]} -gt 0 ]; then
    echo ""
    echo "Issue Summary:"
    for i in "${#ISSUES[@]}"; do
        for issue in "${ISSUES[@]}"; do
            echo "  • $issue"
        done
        break
    done
fi

exit $([ ${#ISSUES[@]} -eq 0 ] && echo 0 || echo 1)
