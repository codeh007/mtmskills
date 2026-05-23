#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$script_dir/.." && pwd)"

prompt="${1:-A clean baseline test image: a red ceramic cup on a white table, soft daylight, realistic photo, no text, no logo.}"
output_dir="${MTM_IMAGE2_OUTPUT_DIR:-$PWD/mtm-image2-output}"
size="${MTM_IMAGE2_SIZE:-1024x1024}"
quality="${MTM_IMAGE2_QUALITY:-medium}"
format="${MTM_IMAGE2_FORMAT:-png}"

python3 "$skill_dir/scripts/mtm_image2.py" \
  --prompt "$prompt" \
  --output-dir "$output_dir" \
  --size "$size" \
  --quality "$quality" \
  --format "$format"
