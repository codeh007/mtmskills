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

OUT_PATH="pkg/clicmd/openapi.json"
TMP_TEST="pkg/openapi_skill_generate_test.go"

cleanup() {
  rm -f "$TMP_TEST"
}
trap cleanup EXIT

mkdir -p "$(dirname "$OUT_PATH")"
cat > "$TMP_TEST" <<'GOEOF'
package pkg

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/codeh007/gomtm/pkg/appcontext"
	"github.com/codeh007/gomtm/pkg/config"
	"github.com/rs/zerolog"
)

func TestSkillGenerateOpenAPISpec(t *testing.T) {
	logger := zerolog.New(os.Stderr)
	appCtx := &appcontext.AppContext{
		Config: &config.RuntimeConfig{
			Server: config.ServerRuntimeConfig{Listen: ":8383"},
		},
		Logger: &logger,
	}
	app := NewMtmBaseApp(appCtx)
	_, err := app.BuildHTTPHandler()
	if err != nil {
		t.Fatalf("build HTTP handler: %v", err)
	}
	data, err := json.MarshalIndent(app.fuegoServer.OpenAPI.Description(), "", "  ")
	if err != nil {
		t.Fatalf("marshal OpenAPI spec: %v", err)
	}
	outPath := filepath.Join("..", "pkg", "clicmd", "openapi.json")
	if err := os.WriteFile(outPath, data, 0o600); err != nil {
		t.Fatalf("write OpenAPI spec: %v", err)
	}
}
GOEOF

GOCACHE="$GO_CACHE" \
go test ./pkg -run '^TestSkillGenerateOpenAPISpec$' -count=1

python3 - <<'PY'
import json
from pathlib import Path
path = Path('pkg/clicmd/openapi.json')
with path.open('r', encoding='utf-8') as f:
    spec = json.load(f)
if not spec.get('openapi'):
    raise SystemExit('missing openapi version')
if not isinstance(spec.get('paths'), dict) or not spec['paths']:
    raise SystemExit('missing OpenAPI paths')
print(f'wrote {path} with {len(spec["paths"])} paths')
PY
