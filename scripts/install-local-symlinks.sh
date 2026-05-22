#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GOMTM_DIR="${GOMTM_DIR:-/workspace/gomtm}"
cd "$GOMTM_DIR"
exec go run ./cmd skills link "$ROOT/skills" \
  --agent hermes-agent,codex,claude-code \
  --hermes-mode symlink \
  --preserve-path \
  "$@"
