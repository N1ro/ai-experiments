#!/bin/bash
# Deploy QA agents globally so they're available in every repo via Claude Code.
# Run this once on any machine after cloning ai-experiments.
#
# Usage:  bash qa-tooling/deploy.sh
#         bash qa-tooling/deploy.sh --dry-run

set -e

AGENTS_DIR="$(cd "$(dirname "$0")/agents" && pwd)"
GLOBAL_DIR="$HOME/.claude/agents"
DRY_RUN=false

[[ "$1" == "--dry-run" ]] && DRY_RUN=true

echo "Source:      $AGENTS_DIR"
echo "Destination: $GLOBAL_DIR"
$DRY_RUN && echo "Mode:        DRY RUN (no files written)"
echo ""

mkdir -p "$GLOBAL_DIR"

for src in "$AGENTS_DIR"/*.md; do
  name=$(basename "$src")
  dst="$GLOBAL_DIR/$name"
  if $DRY_RUN; then
    echo "  would copy: $name → $GLOBAL_DIR/"
  else
    cp "$src" "$dst"
    echo "  ✓ deployed: $name"
  fi
done

echo ""
if $DRY_RUN; then
  echo "Dry run complete. Run without --dry-run to deploy."
else
  echo "Done. Agents are now globally available in every Claude Code session."
  echo ""
  echo "Verify: ls ~/.claude/agents/"
fi
