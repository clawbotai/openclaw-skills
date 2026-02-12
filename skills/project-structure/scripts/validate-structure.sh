#!/usr/bin/env bash
# validate-structure.sh — Validate a project against structure standards
# Usage: bash validate-structure.sh <project-path> [type]
# Types: skill, node-app, python-app, go-app, ml-project, fullstack, generic (default)
# Exit codes: 0 = pass, 1 = warnings, 2 = errors

set -uo pipefail


# --- Auto-injected by master-docs/inject-help.sh ---
show_help() {
    cat <<'ENDHELP'
NAME
    validate-structure — validate-structure.sh — Validate a project against structure standards Usage: bash validate-structure.sh <project-path> [type] Types: skill, node-app, python-app, go-app, ml-project, fullstack, generic (default)

SYNOPSIS
    validate-structure.sh [OPTIONS]

DESCRIPTION
    validate-structure.sh — Validate a project against structure standards Usage: bash validate-structure.sh <project-path> [type] Types: skill, node-app, python-app, go-app, ml-project, fullstack, generic (default)

OPTIONS
    -h, --help    Show this help message and exit

EXIT STATUS
    0   Success
    1   Error
ENDHELP
}

# Parse --help / -h flags
for arg in "$@"; do
    case "$arg" in
        -h|--help) show_help; exit 0 ;;
    esac
done
# --- End auto-injected help ---
PROJECT_PATH="${1:-.}"
PROJECT_TYPE="${2:-generic}"

ERRORS=0
WARNINGS=0

red()    { echo -e "\033[31m✗ $1\033[0m"; }
yellow() { echo -e "\033[33m⚠ $1\033[0m"; }
green()  { echo -e "\033[32m✓ $1\033[0m"; }
blue()   { echo -e "\033[34mℹ $1\033[0m"; }

error()   { red "$1"; ((ERRORS++)); }
warn()    { yellow "$1"; ((WARNINGS++)); }
pass()    { green "$1"; }

echo "═══════════════════════════════════════════"
echo " Project Structure Validation"
echo " Path: $PROJECT_PATH"
echo " Type: $PROJECT_TYPE"
echo "═══════════════════════════════════════════"
echo ""

# --- Universal Checks ---
echo "── Universal Checks ──"

# README
if [ -f "$PROJECT_PATH/README.md" ] || [ -f "$PROJECT_PATH/SKILL.md" ]; then
  pass "Has README.md or SKILL.md"
else
  error "Missing README.md (or SKILL.md for skills)"
fi

# .gitignore (skills inherit parent repo's .gitignore, so skip for skill type)
if [ -f "$PROJECT_PATH/.gitignore" ]; then
  pass "Has .gitignore"
elif [ "$PROJECT_TYPE" = "skill" ]; then
  blue ".gitignore not needed (skills inherit from parent repo)"
else
  warn "Missing .gitignore"
fi

# Anti-pattern: node_modules committed
if [ -d "$PROJECT_PATH/node_modules" ] && [ -d "$PROJECT_PATH/.git" ]; then
  # Check if node_modules is tracked by git
  if cd "$PROJECT_PATH" && git ls-files --error-unmatch node_modules/ &>/dev/null 2>&1; then
    error "node_modules/ is committed to git"
  else
    pass "node_modules/ not tracked by git"
  fi
  cd - &>/dev/null || true
elif [ -d "$PROJECT_PATH/node_modules" ]; then
  warn "node_modules/ exists (verify it's gitignored)"
fi

# Anti-pattern: .env with real secrets
if [ -f "$PROJECT_PATH/.env" ]; then
  if [ -f "$PROJECT_PATH/.gitignore" ] && grep -q "^\.env$\|^\.env\b" "$PROJECT_PATH/.gitignore" 2>/dev/null; then
    pass ".env is gitignored"
  else
    error ".env exists but may not be gitignored — potential secret leak!"
  fi
fi

# Anti-pattern: __pycache__ committed
if find "$PROJECT_PATH" -name "__pycache__" -not -path "*/node_modules/*" -not -path "*/.git/*" | grep -q .; then
  warn "__pycache__/ directories found (should be gitignored)"
fi

# Anti-pattern: dist/build committed
for dir in dist build; do
  if [ -d "$PROJECT_PATH/$dir" ] && [ -d "$PROJECT_PATH/.git" ]; then
    warn "$dir/ directory exists (usually should be gitignored)"
  fi
done

# Check for large files
LARGE_FILES=$(find "$PROJECT_PATH" -type f -size +1M \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/.venv/*" \
  -not -path "*/venv/*" \
  -not -name "*.lock" \
  -not -name "package-lock.json" \
  2>/dev/null | head -5)
if [ -n "$LARGE_FILES" ]; then
  warn "Large files (>1MB) found:"
  echo "$LARGE_FILES" | while read -r f; do
    size=$(du -h "$f" 2>/dev/null | cut -f1)
    echo "    $f ($size)"
  done
fi

# Check for spaces in filenames
SPACE_FILES=$(find "$PROJECT_PATH" -name "* *" \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/.venv/*" \
  2>/dev/null | head -5)
if [ -n "$SPACE_FILES" ]; then
  error "Files/folders with spaces found:"
  echo "$SPACE_FILES" | while read -r f; do echo "    $f"; done
fi

# Nesting depth check
DEEP_FILES=$(find "$PROJECT_PATH" -mindepth 6 -type f \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/.venv/*" \
  2>/dev/null | head -5)
if [ -n "$DEEP_FILES" ]; then
  warn "Deeply nested files (>5 levels):"
  echo "$DEEP_FILES" | while read -r f; do echo "    $f"; done
fi

echo ""

# --- Type-Specific Checks ---
echo "── Type-Specific Checks ($PROJECT_TYPE) ──"

case "$PROJECT_TYPE" in
  skill)
    # SKILL.md required
    if [ -f "$PROJECT_PATH/SKILL.md" ]; then
      pass "Has SKILL.md"
      # Check SKILL.md has content
      lines=$(wc -l < "$PROJECT_PATH/SKILL.md" 2>/dev/null || echo 0)
      if [ "$lines" -lt 5 ]; then
        warn "SKILL.md is very short ($lines lines)"
      fi
    else
      error "Missing SKILL.md (required for skills)"
    fi

    # _meta.json required
    if [ -f "$PROJECT_PATH/_meta.json" ]; then
      pass "Has _meta.json"
      # Validate required fields
      for field in slug version description; do
        if grep -q "\"$field\"" "$PROJECT_PATH/_meta.json" 2>/dev/null; then
          pass "_meta.json has '$field' field"
        else
          error "_meta.json missing required field: $field"
        fi
      done
    else
      error "Missing _meta.json (required for skills)"
    fi
    ;;

  node-app)
    [ -f "$PROJECT_PATH/package.json" ] && pass "Has package.json" || error "Missing package.json"
    [ -f "$PROJECT_PATH/tsconfig.json" ] && pass "Has tsconfig.json" || warn "Missing tsconfig.json (TypeScript recommended)"
    [ -d "$PROJECT_PATH/src" ] && pass "Has src/ directory" || warn "Missing src/ directory (code should not be in root)"
    [ -f "$PROJECT_PATH/.env.example" ] && pass "Has .env.example" || warn "Missing .env.example"
    ;;

  python-app)
    [ -f "$PROJECT_PATH/pyproject.toml" ] && pass "Has pyproject.toml" || warn "Missing pyproject.toml (modern Python standard)"
    [ -d "$PROJECT_PATH/src" ] && pass "Has src/ directory" || warn "Missing src/ layout"
    if [ -f "$PROJECT_PATH/setup.py" ]; then
      warn "setup.py found — consider migrating to pyproject.toml"
    fi
    ;;

  ml-project)
    [ -f "$PROJECT_PATH/pyproject.toml" ] && pass "Has pyproject.toml" || warn "Missing pyproject.toml"
    [ -d "$PROJECT_PATH/src" ] && pass "Has src/ directory" || warn "Missing src/ layout"
    [ -d "$PROJECT_PATH/data" ] && pass "Has data/ directory" || warn "Missing data/ directory"
    [ -d "$PROJECT_PATH/notebooks" ] && pass "Has notebooks/ directory" || blue "No notebooks/ (optional)"
    [ -d "$PROJECT_PATH/configs" ] || [ -d "$PROJECT_PATH/config" ] && pass "Has config directory" || warn "Missing configs/ directory"
    ;;

  fullstack)
    [ -f "$PROJECT_PATH/package.json" ] && pass "Has package.json" || error "Missing package.json"
    [ -d "$PROJECT_PATH/apps" ] && pass "Has apps/ directory" || warn "Missing apps/ (monorepo convention)"
    [ -d "$PROJECT_PATH/packages" ] && pass "Has packages/ directory" || blue "No packages/ (optional)"
    ;;

  go-app)
    [ -f "$PROJECT_PATH/go.mod" ] && pass "Has go.mod" || error "Missing go.mod"
    [ -d "$PROJECT_PATH/cmd" ] && pass "Has cmd/ directory" || warn "Missing cmd/ (standard Go entry point)"
    [ -d "$PROJECT_PATH/internal" ] && pass "Has internal/ directory" || warn "Missing internal/ (private packages)"
    ;;

  generic|*)
    blue "Generic validation only (use a specific type for deeper checks)"
    ;;
esac

echo ""
echo "═══════════════════════════════════════════"
echo " Results: $ERRORS error(s), $WARNINGS warning(s)"
echo "═══════════════════════════════════════════"

if [ "$ERRORS" -gt 0 ]; then
  exit 2
elif [ "$WARNINGS" -gt 0 ]; then
  exit 1
else
  echo ""
  green "All checks passed!"
  exit 0
fi
