#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$script_dir/.." && pwd)"

prompt="${1:-A high-resolution editorial product photograph of a matte black desk lamp on a walnut desk, realistic studio lighting, crisp details, no text, no logo.}"
output_dir="${MTM_IMAGE2_OUTPUT_DIR:-$PWD/mtm-image2-output}"
size="${MTM_IMAGE2_SIZE:-2048x2048}"
quality="${MTM_IMAGE2_QUALITY:-high}"
format="${MTM_IMAGE2_FORMAT:-jpeg}"
partial_images="${MTM_IMAGE2_PARTIAL_IMAGES:-2}"

python3 "$skill_dir/scripts/mtm_image2.py" \
  --prompt "$prompt" \
  --output-dir "$output_dir" \
  --size "$size" \
  --quality "$quality" \
  --format "$format" \
  --stream \
  --partial-images "$partial_images"
