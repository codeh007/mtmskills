#!/usr/bin/env bash
# ABOUTME: Splits categorized function catalog entries into per-category JSON files.

set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") <categorized-json> <output-dir>

Split a categorized function catalog into one JSON file per category.

INPUT FORMAT:
    JSON array of objects containing at least: file, name, line, category, purpose

EXAMPLE:
    $(basename "$0") categorized.json ./categories
EOF
    exit 0
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
fi

if [[ -z "${1:-}" || -z "${2:-}" ]]; then
    echo "Error: categorized JSON and output directory are required" >&2
    usage
fi

INPUT="$1"
OUTPUT_DIR="$2"

if [[ ! -f "$INPUT" ]]; then
    echo "Error: file not found: $INPUT" >&2
    exit 1
fi

if ! jq -e 'type == "array"' "$INPUT" >/dev/null; then
    echo "Error: input must be a JSON array: $INPUT" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

jq -r '[.[].category // "other"] | unique[]' "$INPUT" | while IFS= read -r category; do
    [[ -n "$category" ]] || continue
    safe_category=$(printf '%s' "$category" | tr -cs 'A-Za-z0-9._-' '-' | sed 's/^-//; s/-$//')
    [[ -n "$safe_category" ]] || safe_category="other"

    jq --arg category "$category" '
        [.[] | select((.category // "other") == $category)]
        | sort_by(.file, .line, .name)
    ' "$INPUT" > "$OUTPUT_DIR/$safe_category.json"
done

count=$(find "$OUTPUT_DIR" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')
echo "Wrote $count category files to $OUTPUT_DIR" >&2
