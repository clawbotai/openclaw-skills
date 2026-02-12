#!/usr/bin/env bash
# Fix _meta.json files to include description field
set -euo pipefail

for skill in skills/*/; do
    [ ! -f "$skill/_meta.json" ] && continue
    name=$(basename "$skill")
    
    # Check if description already exists
    if grep -q '"description"' "$skill/_meta.json"; then
        continue
    fi
    
    # Get description from SKILL.md
    desc=$(sed -n '/^---$/,/^---$/{ /^description:/{ s/^description: *//; s/^["'"'"']//; s/["'"'"']$//; p; q; } }' "$skill/SKILL.md" 2>/dev/null || true)
    if [ -z "$desc" ] || [ ${#desc} -lt 10 ] || echo "$desc" | grep -qiE '(metadata|homepage|triggers|allowed-tools|version|model|user-invocable|author)'; then
        desc="OpenClaw skill for ${name//-/ } workflows."
    fi
    # Escape quotes
    desc=$(echo "$desc" | sed 's/"/\\"/g')
    
    # Add description field after slug
    sed -i "s/\"slug\": \"$name\"/\"slug\": \"$name\",\n  \"description\": \"$desc\"/" "$skill/_meta.json"
    echo "Fixed: $name"
done
