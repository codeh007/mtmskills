#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
if ! grep -qx 'module github.com/codeh007/gomtm' "$ROOT_DIR/go.mod"; then
  echo "resolved repo root is not gomtm: $ROOT_DIR" >&2
  exit 2
fi
cd "$ROOT_DIR"
GO_CACHE="${GOCACHE:-$(go env GOCACHE)}"
case "$(realpath -m "$GO_CACHE")" in
  "$ROOT_DIR/.agents"|"$ROOT_DIR/.agents"/*)
    echo "refusing to use GOCACHE inside .agents; fix go env GOCACHE or unset GOCACHE" >&2
    exit 2
    ;;
esac

OUT_DIR="${1:-}"
if [[ -z "$OUT_DIR" ]]; then
  echo "usage: $0 <output-dir-outside-gomtm-or-temp>" >&2
  exit 2
fi

case "$(realpath -m "$OUT_DIR")" in
  "$ROOT_DIR"|"$ROOT_DIR"/*)
    echo "refusing to generate optional client inside gomtm repo: $OUT_DIR" >&2
    exit 2
    ;;
esac

mkdir -p "$OUT_DIR"
cat > "$OUT_DIR/codegen.yaml" <<YAML
package: rest_v2
output: $OUT_DIR/apiv2client_gen.go
generate:
  models: true
  client: true
YAML

GOCACHE="$GO_CACHE" \
go run github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@v2.5.0 \
  -config "$OUT_DIR/codegen.yaml" \
  ./pkg/clicmd/openapi.json

gofmt -w "$OUT_DIR/apiv2client_gen.go"
echo "wrote $OUT_DIR/apiv2client_gen.go"
