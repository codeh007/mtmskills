#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${HERMES_MODEL_BASE_URL:-}"
API_KEY="${HERMES_MODEL_API_KEY:-}"
MODEL="${HERMES_MODEL:-${1:-}}"

if [[ -z "$BASE_URL" ]]; then
  echo "HERMES_MODEL_BASE_URL is required" >&2
  exit 2
fi
if [[ -z "$API_KEY" ]]; then
  echo "HERMES_MODEL_API_KEY is required" >&2
  exit 2
fi
if [[ -z "$MODEL" ]]; then
  echo "model is required: set HERMES_MODEL or pass as first argument" >&2
  exit 2
fi

BASE_URL="${BASE_URL%/}"
TMP_DIR="${TMPDIR:-/tmp}"
MODELS_OUT="$(mktemp "$TMP_DIR/hermes-models.XXXXXX.json")"
CHAT_OUT="$(mktemp "$TMP_DIR/hermes-chat.XXXXXX.json")"
trap 'rm -f "$MODELS_OUT" "$CHAT_OUT"' EXIT

models_status="$({ curl -sS -o "$MODELS_OUT" -w '%{http_code}' \
  -H "Authorization: Bearer $API_KEY" \
  "$BASE_URL/models" || true; })"

echo "models_status=$models_status"
if [[ "$models_status" =~ ^2 ]]; then
  python3 - "$MODELS_OUT" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path, 'r', encoding='utf-8'))
items = data.get('data', []) if isinstance(data, dict) else []
ids = [str(x.get('id', '')) for x in items if isinstance(x, dict)]
print('models_count=%d' % len(ids))
for item in ids[:20]:
    print('model=' + item)
PY
else
  echo "models_probe_body_preview=$(head -c 300 "$MODELS_OUT" | tr '\n' ' ')"
fi

payload="$(python3 - "$MODEL" <<'PY'
import json, sys
model = sys.argv[1]
print(json.dumps({
    'model': model,
    'messages': [{'role': 'user', 'content': 'Reply with OK'}],
    'max_tokens': 16,
}, ensure_ascii=False))
PY
)"

chat_status="$({ curl -sS -o "$CHAT_OUT" -w '%{http_code}' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'Content-Type: application/json' \
  -d "$payload" \
  "$BASE_URL/chat/completions" || true; })"

echo "chat_status=$chat_status"
if [[ ! "$chat_status" =~ ^2 ]]; then
  echo "chat_body_preview=$(head -c 600 "$CHAT_OUT" | tr '\n' ' ')" >&2
  exit 1
fi
python3 - "$CHAT_OUT" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path, 'r', encoding='utf-8'))
choices = data.get('choices') or []
content = ''
if choices:
    msg = choices[0].get('message') or {}
    content = msg.get('content') or ''
print('chat_content_preview=' + content[:200].replace('\n', ' '))
PY
