#!/usr/bin/env bash
set -euo pipefail

for skill in skills/*/; do
    [ ! -f "$skill/_meta.json" ] && continue
    name=$(basename "$skill")
    
    if grep -q '"description"' "$skill/_meta.json"; then
        continue
    fi
    
    desc="OpenClaw skill for ${name//-/ } workflows and automation."
    
    # Use a temp file approach - add description after first {
    tmpf=$(mktemp)
    awk -v desc="$desc" '
        /^\{/ { print; printf "  \"description\": \"%s\",\n", desc; next }
        { print }
    ' "$skill/_meta.json" > "$tmpf"
    cp "$tmpf" "$skill/_meta.json"
    rm -f "$tmpf"
    echo "Fixed: $name"
done
