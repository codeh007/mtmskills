#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
if ! grep -qx 'module github.com/codeh007/gomtm' "$ROOT_DIR/go.mod"; then
  echo "resolved repo root is not gomtm: $ROOT_DIR" >&2
  exit 2
fi
GO_CACHE="${GOCACHE:-$(go env GOCACHE)}"
case "$(realpath -m "$GO_CACHE")" in
  "$ROOT_DIR/.agents"|"$ROOT_DIR/.agents"/*)
    echo "refusing to use GOCACHE inside .agents; fix go env GOCACHE or unset GOCACHE" >&2
    exit 2
    ;;
esac

bash "$SCRIPT_DIR/generate-openapi.sh"

if [[ "${GOMTM_GENERATE_REST_CLIENT:-}" != "" ]]; then
  bash "$SCRIPT_DIR/generate-rest-client.sh" "$GOMTM_GENERATE_REST_CLIENT"
fi

cd "$ROOT_DIR"
GOCACHE="$GO_CACHE" \
go test ./pkg/clicmd ./cmd -count=1
