#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Create a timestamped Cloudflare Tunnel incident note template.

Usage: incident-note.sh [--name NAME] [--dir PATH] [--title TEXT]
USAGE
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

name="${CF_TUNNEL_NAME:-}"
tunnel_home="${CF_TUNNEL_HOME:-}"
title="Cloudflare Tunnel incident"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name) name="${2:?missing --name value}"; shift 2 ;;
    --dir) tunnel_home="${2:?missing --dir value}"; shift 2 ;;
    --title) title="${2:?missing --title value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [ -z "$tunnel_home" ]; then
  [ -n "$name" ] || die "--name or --dir is required"
  tunnel_home="${CF_TUNNELS_HOME:-$HOME/.cloudflared-tunnels}/$name"
fi

mkdir -p "$tunnel_home/incidents"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
note="$tunnel_home/incidents/$stamp.md"

cat > "$note" <<NOTE
# $title

- Incident time UTC: $stamp
- Target host:
- Tunnel root: $tunnel_home
- Public hostname:
- Origin URL:
- Tunnel name / ID:
- Systemd unit:
- Impact:
- Data loss status: not expected for tunnel-only incident unless origin service was changed

## Timeline

- 

## Evidence Collected

- Local origin check:
- cloudflared process list:
- systemd status:
- cloudflared logs:
- ingress rule:
- Cloudflare tunnel API status:
- DNS record state:
- Public URL check:

## Root Cause

- 

## Actions Taken

- 

## Verification

- Config validation:
- Local origin:
- Public URL:
- Unaffected hostnames:
- Reboot / restart persistence:

## Follow-ups

- 

## Secret Handling

No secret values are recorded in this note. Secret locations and rotation steps only:

- 
NOTE

printf '%s\n' "$note"
