#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Create a read-only Cloudflare Tunnel inventory report.

Usage: inventory.sh [--name NAME] [--dir PATH]

Defaults:
  --dir $CF_TUNNEL_HOME, or $CF_TUNNELS_HOME/NAME, or ~/.cloudflared-tunnels/NAME
USAGE
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

name="${CF_TUNNEL_NAME:-}"
tunnel_home="${CF_TUNNEL_HOME:-}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name) name="${2:?missing --name value}"; shift 2 ;;
    --dir) tunnel_home="${2:?missing --dir value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [ -z "$tunnel_home" ]; then
  [ -n "$name" ] || die "--name or --dir is required"
  tunnel_home="${CF_TUNNELS_HOME:-$HOME/.cloudflared-tunnels}/$name"
fi

[ -d "$tunnel_home" ] || die "tunnel directory not found: $tunnel_home"
mkdir -p "$tunnel_home/reports"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
report="$tunnel_home/reports/inventory-$stamp.md"
config_file="${CF_TUNNEL_CONFIG:-$tunnel_home/config.yml}"
env_file="$tunnel_home/.env"

extract_first() {
  key="$1"
  file="$2"
  [ -f "$file" ] || return 0
  awk -v key="$key" '$1 == key {print $2; exit}' "$file"
}

extract_hostnames() {
  [ -f "$config_file" ] || return 0
  awk '$1 == "-" && $2 == "hostname:" {print $3} $1 == "hostname:" {print $2}' "$config_file" | sed '/^$/d'
}

extract_services() {
  [ -f "$config_file" ] || return 0
  awk '$1 == "service:" {print $2} $1 == "-" && $2 == "service:" {print $3}' "$config_file" | sed '/^http_status:/d;/^$/d'
}

unit_name=""
if [ -f "$env_file" ]; then
  unit_name="$(awk -F= '$1 == "CF_TUNNEL_SYSTEMD_UNIT" {print $2; exit}' "$env_file")"
fi
if [ -z "$unit_name" ] && [ -n "$name" ]; then
  unit_name="cloudflared-${name}.service"
fi

{
  printf '# Cloudflare Tunnel Inventory %s\n\n' "$stamp"
  printf '## Target\n\n'
  printf -- '- Hostname: `%s`\n' "$(hostname 2>/dev/null || true)"
  printf -- '- Kernel: `%s`\n' "$(uname -a 2>/dev/null || true)"
  printf -- '- Tunnel root: `%s`\n' "$tunnel_home"
  printf -- '- Config file: `%s`\n' "$config_file"
  printf -- '- Env file: `%s`\n' "$env_file"
  printf -- '- Unit: `%s`\n\n' "$unit_name"

  printf '## cloudflared\n\n```text\n'
  cloudflared --version 2>&1 || true
  printf '\n```\n\n'

  printf '## Config Summary\n\n'
  printf -- '- Tunnel: `%s`\n' "$(extract_first tunnel: "$config_file")"
  printf -- '- Credentials file: `%s`\n' "$(extract_first credentials-file: "$config_file")"
  printf '\n### Hostnames\n\n'
  host_count=0
  while IFS= read -r hostname; do
    [ -n "$hostname" ] || continue
    host_count=$((host_count + 1))
    printf -- '- `%s`\n' "$hostname"
  done <<HOSTS
$(extract_hostnames)
HOSTS
  [ "$host_count" -gt 0 ] || printf -- '- none found\n'
  printf '\n### Origins\n\n'
  service_count=0
  while IFS= read -r service; do
    [ -n "$service" ] || continue
    service_count=$((service_count + 1))
    printf -- '- `%s`\n' "$service"
  done <<SERVICES
$(extract_services)
SERVICES
  [ "$service_count" -gt 0 ] || printf -- '- none found\n'

  printf '\n## Secret Inventory\n\n'
  if [ -f "$env_file" ]; then
    awk -F= '/^[A-Z0-9_]+=/{print "- `" $1 "`: " (($2 == "") ? "empty" : "set")}' "$env_file"
  else
    printf -- '- env file missing\n'
  fi
  credentials_path="$(extract_first credentials-file: "$config_file")"
  if [ -n "$credentials_path" ]; then
    if [ -f "$credentials_path" ]; then
      mode="$(stat -c '%a %U:%G' "$credentials_path" 2>/dev/null || true)"
      printf -- '- credentials file: exists `%s` `%s`\n' "$credentials_path" "$mode"
    else
      printf -- '- credentials file: missing `%s`\n' "$credentials_path"
    fi
  fi

  printf '\n## Processes\n\n```text\n'
  pgrep -a cloudflared 2>/dev/null || true
  printf '\n```\n\n'

  printf '## Systemd\n\n```text\n'
  if [ -n "$unit_name" ]; then
    systemctl --user status "$unit_name" --no-pager 2>&1 || true
    systemctl status "$unit_name" --no-pager 2>&1 || true
  fi
  systemctl list-units --type=service --all 'cloudflared*' 2>&1 || true
  printf '\n```\n\n'

  printf '## Config Validation\n\n```text\n'
  if [ -f "$config_file" ]; then
    cloudflared tunnel ingress validate --config "$config_file" 2>&1 || true
    while IFS= read -r hostname; do
      [ -n "$hostname" ] || continue
      cloudflared tunnel ingress rule --config "$config_file" "https://$hostname/" 2>&1 || true
    done <<HOSTS
$(extract_hostnames)
HOSTS
  else
    printf 'config file missing\n'
  fi
  printf '\n```\n\n'

  printf '## Host Resources\n\n```text\n'
  df -h "$tunnel_home" 2>&1 || true
  ss -ltnp 2>/dev/null || true
  printf '\n```\n'
} > "$report"

printf '%s\n' "$report"
