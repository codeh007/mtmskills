#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Query Cloudflare Tunnel and DNS state using read-only API calls.

Usage: cf-state.sh [--env-file PATH] [--account-id ID] [--zone-id ID] [--name NAME] [--hostname FQDN]

Recognized env variables:
  CLOUDFLARE_API_TOKEN or CF_API_TOKEN
  CLOUDFLARE_ACCOUNT_ID or CF_ACCOUNT_ID
  CLOUDFLARE_ZONE_ID or CF_ZONE_ID
USAGE
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"; }

env_file=""
account_id="${CLOUDFLARE_ACCOUNT_ID:-${CF_ACCOUNT_ID:-}}"
zone_id="${CLOUDFLARE_ZONE_ID:-${CF_ZONE_ID:-}}"
api_token="${CLOUDFLARE_API_TOKEN:-${CF_API_TOKEN:-}}"
name="${CF_TUNNEL_NAME:-}"
hostname="${CF_TUNNEL_HOSTNAME:-}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --env-file) env_file="${2:?missing --env-file value}"; shift 2 ;;
    --account-id) account_id="${2:?missing --account-id value}"; shift 2 ;;
    --zone-id) zone_id="${2:?missing --zone-id value}"; shift 2 ;;
    --name) name="${2:?missing --name value}"; shift 2 ;;
    --hostname) hostname="${2:?missing --hostname value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [ -n "$env_file" ]; then
  [ -f "$env_file" ] || die "env file not found: $env_file"
  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
  account_id="${account_id:-${CLOUDFLARE_ACCOUNT_ID:-${CF_ACCOUNT_ID:-}}}"
  zone_id="${zone_id:-${CLOUDFLARE_ZONE_ID:-${CF_ZONE_ID:-}}}"
  api_token="${api_token:-${CLOUDFLARE_API_TOKEN:-${CF_API_TOKEN:-}}}"
fi

[ -n "$api_token" ] || die "Cloudflare API token is required"
[ -n "$account_id" ] || die "Cloudflare account ID is required"

need curl
need jq

api() {
  path="$1"
  curl -fsS "https://api.cloudflare.com/client/v4$path" -H "Authorization: Bearer $api_token"
}

printf '== Tunnels ==\n'
tunnel_query="/accounts/$account_id/cfd_tunnel?per_page=100&is_deleted=false"
if [ -n "$name" ]; then
  tunnel_query="$tunnel_query&name=$(printf '%s' "$name" | jq -sRr @uri)"
fi
api "$tunnel_query" | jq '.result[] | {id, name, status, config_src, remote_config, conns_active_at, conns_inactive_at, connections: (.connections // []) | length, metadata}'

if [ -n "$hostname" ]; then
  [ -n "$zone_id" ] || die "zone ID is required when --hostname is used"
  printf '\n== DNS records for %s ==\n' "$hostname"
  encoded_hostname="$(printf '%s' "$hostname" | jq -sRr @uri)"
  api "/zones/$zone_id/dns_records?name=$encoded_hostname&per_page=100" | jq '.result[] | {id, type, name, content, proxied, comment, tags}'
fi
