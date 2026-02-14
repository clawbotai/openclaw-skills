#!/usr/bin/env bash
# Update OpenClaw Knowledge Base
# Fetches latest docs from docs.openclaw.ai and updates local copies
# Usage: bash scripts/update-kb.sh

set -euo pipefail

DOCS_DIR="$(dirname "$0")/../docs"
BASE_URL="https://docs.openclaw.ai"

PAGES=(
  "/gateway:gateway-runbook.md"
  "/gateway/configuration-reference:configuration-reference.md"
  "/gateway/security:security.md"
  "/gateway/sandboxing:sandboxing.md"
  "/tools/multi-agent-sandbox-tools:multi-agent-sandbox-tools.md"
  "/concepts/models:models.md"
  "/concepts/multi-agent:multi-agent.md"
  "/concepts/session:sessions.md"
  "/tools/slash-commands:slash-commands.md"
  "/tools/skills:skills.md"
  "/tools/plugin:plugins.md"
  "/concepts/compaction:compaction.md"
  "/install/updating:updating.md"
  "/help/faq:faq-summary.md"
)

echo "OpenClaw KB Updater"
echo "==================="
echo "Docs dir: $DOCS_DIR"
echo "Pages to fetch: ${#PAGES[@]}"
echo ""
echo "NOTE: This script lists the pages to update."
echo "Actual fetching should be done via the agent's web_fetch tool"
echo "since curl may not extract readable content from JS-rendered pages."
echo ""

for entry in "${PAGES[@]}"; do
  path="${entry%%:*}"
  file="${entry##*:}"
  echo "  $BASE_URL$path → $file"
done

echo ""
echo "To update, ask the agent: 'Update the openclaw-kb skill docs'"
