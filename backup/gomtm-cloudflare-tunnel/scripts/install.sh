#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Prepare an auditable per-service Cloudflare Tunnel root.

Usage: install.sh --name NAME --hostname FQDN --origin URL [options]

Options:
  --dir PATH              Service tunnel root. Default: $CF_TUNNELS_HOME/NAME or ~/.cloudflared-tunnels/NAME
  --tunnel-id UUID        Existing locally-managed tunnel UUID
  --credentials-file PATH Existing locally-managed tunnel credentials JSON to copy
  --create-tunnel         Run 'cloudflared tunnel create NAME' if no tunnel-id is provided
  --route-dns             Run 'cloudflared tunnel route dns TUNNEL HOSTNAME'
  --systemd user|system|none  Write a systemd unit. Default: user
  --start                 Start the written systemd unit after validation
  --force                 Allow overwriting generated config.yml and README.MD

This script does not copy Cloudflare account tokens to the target host.
USAGE
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"; }

safe_name() {
  case "$1" in
    ''|*[!a-zA-Z0-9._-]*) return 1 ;;
    *) return 0 ;;
  esac
}

name="${CF_TUNNEL_NAME:-}"
hostname="${CF_TUNNEL_HOSTNAME:-}"
origin="${CF_TUNNEL_ORIGIN:-}"
home_arg="${CF_TUNNEL_HOME:-}"
tunnel_id="${CF_TUNNEL_ID:-}"
credentials_file="${CF_TUNNEL_CREDENTIALS_FILE:-}"
create_tunnel=0
route_dns=0
systemd_mode="${CF_TUNNEL_SYSTEMD:-user}"
start_unit=0
force=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name) name="${2:?missing --name value}"; shift 2 ;;
    --hostname) hostname="${2:?missing --hostname value}"; shift 2 ;;
    --origin) origin="${2:?missing --origin value}"; shift 2 ;;
    --dir) home_arg="${2:?missing --dir value}"; shift 2 ;;
    --tunnel-id) tunnel_id="${2:?missing --tunnel-id value}"; shift 2 ;;
    --credentials-file) credentials_file="${2:?missing --credentials-file value}"; shift 2 ;;
    --create-tunnel) create_tunnel=1; shift ;;
    --route-dns) route_dns=1; shift ;;
    --systemd) systemd_mode="${2:?missing --systemd value}"; shift 2 ;;
    --start) start_unit=1; shift ;;
    --force) force=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$name" ] || die "--name is required"
[ -n "$hostname" ] || die "--hostname is required"
[ -n "$origin" ] || die "--origin is required"
safe_name "$name" || die "name may contain only letters, numbers, dot, underscore, and dash"
case "$hostname" in *.*) ;; *) die "hostname must be a fully qualified domain name" ;; esac
case "$origin" in http://*|https://*) ;; *) die "origin must start with http:// or https://" ;; esac
case "$systemd_mode" in user|system|none) ;; *) die "--systemd must be user, system, or none" ;; esac

need cloudflared
need curl

tunnels_home="${CF_TUNNELS_HOME:-$HOME/.cloudflared-tunnels}"
tunnel_home="${home_arg:-$tunnels_home/$name}"
mkdir -p "$tunnel_home" "$tunnel_home/credentials" "$tunnel_home/reports" "$tunnel_home/incidents" "$tunnel_home/scripts"
chmod 700 "$tunnel_home" "$tunnel_home/credentials"

config_file="$tunnel_home/config.yml"
env_file="$tunnel_home/.env"
readme_file="$tunnel_home/README.MD"
registry_file="$(dirname "$tunnel_home")/REGISTRY.md"
unit_name="cloudflared-${name}.service"

if [ "$create_tunnel" -eq 1 ] && [ -z "$tunnel_id" ]; then
  cloudflared tunnel create "$name"
  if command -v jq >/dev/null 2>&1; then
    tunnel_id="$(cloudflared tunnel list --name "$name" --output json | jq -r --arg name "$name" '.[] | select(.name == $name) | .id' | head -n 1)"
  else
    printf 'WARNING: jq is missing; pass --tunnel-id explicitly if tunnel ID was not detected.\n' >&2
  fi
fi

if [ -z "$tunnel_id" ] && [ -n "$credentials_file" ]; then
  tunnel_id="$(basename "$credentials_file" .json)"
fi
[ -n "$tunnel_id" ] || die "provide --tunnel-id/--credentials-file or use --create-tunnel with jq available"

target_credentials="$tunnel_home/credentials/${tunnel_id}.json"
if [ -n "$credentials_file" ]; then
  [ -f "$credentials_file" ] || die "credentials file not found: $credentials_file"
  cp "$credentials_file" "$target_credentials"
  chmod 600 "$target_credentials"
elif [ -f "$HOME/.cloudflared/${tunnel_id}.json" ]; then
  cp "$HOME/.cloudflared/${tunnel_id}.json" "$target_credentials"
  chmod 600 "$target_credentials"
elif [ ! -f "$target_credentials" ]; then
  die "credentials JSON not found; pass --credentials-file or copy it to $target_credentials"
fi

if [ "$route_dns" -eq 1 ]; then
  cloudflared tunnel route dns "$tunnel_id" "$hostname"
fi

if [ -f "$config_file" ] && [ "$force" -ne 1 ]; then
  die "config already exists: $config_file (use --force to overwrite generated config)"
fi

cat > "$config_file" <<YAML
tunnel: $tunnel_id
credentials-file: $target_credentials

ingress:
  - hostname: $hostname
    service: $origin
  - service: http_status:404
YAML
chmod 600 "$config_file"

cat > "$env_file" <<ENV
CF_TUNNEL_NAME=$name
CF_TUNNEL_ID=$tunnel_id
CF_TUNNEL_HOSTNAME=$hostname
CF_TUNNEL_ORIGIN=$origin
CF_TUNNEL_CONFIG=$config_file
CF_TUNNEL_CREDENTIALS=$target_credentials
CF_TUNNEL_SYSTEMD_UNIT=$unit_name
ENV
chmod 600 "$env_file"

cloudflared tunnel ingress validate --config "$config_file"

if [ ! -f "$readme_file" ] || [ "$force" -eq 1 ]; then
  cat > "$readme_file" <<README
# Cloudflare Tunnel: $name

Do not record secret values in this file.

## Mapping

- Public URL: https://$hostname
- Origin URL: $origin
- Tunnel name: $name
- Tunnel ID: $tunnel_id
- Config source: local
- Config path: $config_file
- Credential path: $target_credentials
- Systemd unit: $unit_name

## Commands

- Validate config: \`cloudflared tunnel ingress validate --config $config_file\`
- Show matching rule: \`cloudflared tunnel ingress rule --config $config_file https://$hostname/\`
- Check local origin: \`curl -fsS $origin\`
- Check public URL: \`curl -fsS https://$hostname\`
- User unit status: \`systemctl --user status $unit_name\`
- System unit status: \`systemctl status $unit_name\`
- Logs: \`journalctl --user -u $unit_name --since '30 minutes ago' --no-pager\`

## Change Procedure

1. Run \`scripts/inventory.sh --name $name\` before changes.
2. Change only the hostname rule that maps to this service.
3. Run config validation and health checks.
4. Restart only \`$unit_name\`.
5. Update this README with the new origin, hostname, and last verified time.

## Last Verification

- Time UTC: TODO
- Operator: TODO
- Local origin: TODO
- Public URL: TODO
- Cloudflare tunnel status: TODO
README
fi

if [ ! -f "$registry_file" ]; then
  cat > "$registry_file" <<'REGISTRY'
# Cloudflare Tunnel Registry

Do not record secret values in this file.

| Service | Public hostname | Origin URL | Health path | Tunnel name | Tunnel ID | Config source | Tunnel root | Unit | Owner | Last verified UTC | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
REGISTRY
fi
if ! grep -F "| $name | $hostname |" "$registry_file" >/dev/null 2>&1; then
  printf '| %s | %s | %s | TODO | %s | %s | local | %s | %s | TODO | TODO | generated by install.sh |\n' "$name" "$hostname" "$origin" "$name" "$tunnel_id" "$tunnel_home" "$unit_name" >> "$registry_file"
fi

cloudflared_path="$(command -v cloudflared)"
if [ "$systemd_mode" = "user" ]; then
  unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir"
  unit_file="$unit_dir/$unit_name"
  cat > "$unit_file" <<UNIT
[Unit]
Description=Cloudflare Tunnel for $name ($hostname)
After=network-online.target

[Service]
Type=simple
ExecStart=$cloudflared_path tunnel --config $config_file run
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
UNIT
  systemctl --user daemon-reload || printf 'WARNING: systemctl --user daemon-reload failed; enable/start manually.\n' >&2
  systemctl --user enable "$unit_name" || printf 'WARNING: systemctl --user enable failed; enable manually.\n' >&2
  [ "$start_unit" -eq 1 ] && systemctl --user restart "$unit_name"
elif [ "$systemd_mode" = "system" ]; then
  [ "$(id -u)" -eq 0 ] || die "--systemd system must be run as root"
  unit_file="/etc/systemd/system/$unit_name"
  cat > "$unit_file" <<UNIT
[Unit]
Description=Cloudflare Tunnel for $name ($hostname)
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=$cloudflared_path tunnel --config $config_file run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
  systemctl daemon-reload
  systemctl enable "$unit_name"
  [ "$start_unit" -eq 1 ] && systemctl restart "$unit_name"
fi

printf 'Prepared Cloudflare Tunnel root: %s\n' "$tunnel_home"
printf 'Config: %s\n' "$config_file"
printf 'README: %s\n' "$readme_file"
