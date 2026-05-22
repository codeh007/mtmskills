#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Run local and public Cloudflare Tunnel health checks.

Usage: healthcheck.sh [--name NAME] [--dir PATH] [--path PATH] [--public-url URL] [--origin URL]
USAGE
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

name="${CF_TUNNEL_NAME:-}"
tunnel_home="${CF_TUNNEL_HOME:-}"
health_path="/"
public_url=""
origin_override=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name) name="${2:?missing --name value}"; shift 2 ;;
    --dir) tunnel_home="${2:?missing --dir value}"; shift 2 ;;
    --path) health_path="${2:?missing --path value}"; shift 2 ;;
    --public-url) public_url="${2:?missing --public-url value}"; shift 2 ;;
    --origin) origin_override="${2:?missing --origin value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [ -z "$tunnel_home" ]; then
  [ -n "$name" ] || die "--name or --dir is required"
  tunnel_home="${CF_TUNNELS_HOME:-$HOME/.cloudflared-tunnels}/$name"
fi

config_file="${CF_TUNNEL_CONFIG:-$tunnel_home/config.yml}"
env_file="$tunnel_home/.env"
[ -f "$config_file" ] || die "config file not found: $config_file"

first_hostname="$(awk '$1 == "-" && $2 == "hostname:" {print $3; exit} $1 == "hostname:" {print $2; exit}' "$config_file")"
first_origin="$(awk '$1 == "service:" && $2 !~ /^http_status:/ {print $2; exit} $1 == "-" && $2 == "service:" && $3 !~ /^http_status:/ {print $3; exit}' "$config_file")"
origin="${origin_override:-$first_origin}"
[ -n "$public_url" ] || [ -z "$first_hostname" ] || public_url="https://$first_hostname$health_path"
case "$origin" in
  http://*|https://*) origin_url="${origin%/}$health_path" ;;
  *) origin_url="" ;;
esac

unit_name=""
if [ -f "$env_file" ]; then
  unit_name="$(awk -F= '$1 == "CF_TUNNEL_SYSTEMD_UNIT" {print $2; exit}' "$env_file")"
fi
if [ -z "$unit_name" ] && [ -n "$name" ]; then
  unit_name="cloudflared-${name}.service"
fi

status=0

printf '== cloudflared version ==\n'
cloudflared --version || status=1

printf '\n== Config validation ==\n'
cloudflared tunnel ingress validate --config "$config_file" || status=1

if [ -n "$first_hostname" ]; then
  printf '\n== Ingress rule ==\n'
  cloudflared tunnel ingress rule --config "$config_file" "https://$first_hostname$health_path" || status=1
fi

if [ -n "$origin_url" ]; then
  printf '\n== Local origin ==\n'
  curl -fsS "$origin_url" || status=1
  printf '\n'
else
  printf '\n== Local origin ==\nSkipping non-HTTP origin: %s\n' "$origin"
fi

if [ -n "$public_url" ]; then
  printf '\n== Public URL ==\n'
  curl -fsS "$public_url" || status=1
  printf '\n'
fi

if [ -n "$unit_name" ]; then
  printf '\n== Systemd user unit ==\n'
  systemctl --user status "$unit_name" --no-pager || true
  printf '\n== Systemd system unit ==\n'
  systemctl status "$unit_name" --no-pager || true
fi

printf '\n== Recent logs ==\n'
if [ -n "$unit_name" ]; then
  journalctl --user -u "$unit_name" --since '30 minutes ago' --no-pager 2>/dev/null || true
  journalctl -u "$unit_name" --since '30 minutes ago' --no-pager 2>/dev/null || true
fi

exit "$status"
